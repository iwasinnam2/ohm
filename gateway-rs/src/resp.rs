//! Lightweight RESP encoder/decoder for Redis over TCP.

use anyhow::{anyhow, Result};
use bytes::BytesMut;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpStream;

#[derive(Debug, Clone, PartialEq)]
pub enum RespValue {
    Simple(String),
    Error(String),
    Integer(i64),
    Bulk(Option<String>),
    Array(Vec<RespValue>),
}

pub struct RespClient {
    stream: TcpStream,
    buf: BytesMut,
}

impl RespClient {
    pub async fn connect(addr: &str) -> Result<Self> {
        let stream = tokio::time::timeout(
            std::time::Duration::from_secs(2),
            TcpStream::connect(addr),
        )
        .await
        .map_err(|_| anyhow!("redis connect timeout to {addr}"))?
        .map_err(|e| anyhow!("redis connect to {addr}: {e}"))?;
        Ok(Self {
            stream,
            buf: BytesMut::with_capacity(4096),
        })
    }

    pub fn encode_command(args: &[&str]) -> Vec<u8> {
        let mut out = format!("*{}\r\n", args.len()).into_bytes();
        for a in args {
            out.extend_from_slice(format!("${}\r\n{}\r\n", a.as_bytes().len(), a).as_bytes());
        }
        out
    }

    pub async fn command(&mut self, args: &[&str]) -> Result<RespValue> {
        let payload = Self::encode_command(args);
        tokio::time::timeout(std::time::Duration::from_secs(2), self.stream.write_all(&payload))
            .await
            .map_err(|_| anyhow!("redis write timeout"))?
            .map_err(|e| anyhow!("redis write: {e}"))?;
        tokio::time::timeout(std::time::Duration::from_secs(2), self.read_value())
            .await
            .map_err(|_| anyhow!("redis read timeout"))?
    }

    pub async fn get(&mut self, key: &str) -> Result<Option<String>> {
        match self.command(&["GET", key]).await? {
            RespValue::Bulk(v) => Ok(v),
            RespValue::Simple(s) => Ok(Some(s)),
            RespValue::Error(e) => Err(anyhow!(e)),
            other => Err(anyhow!("unexpected GET response: {:?}", other)),
        }
    }

    pub async fn set_ex(&mut self, key: &str, value: &str, ttl: u64) -> Result<()> {
        let ttl_s = ttl.to_string();
        match self.command(&["SET", key, value, "EX", &ttl_s]).await? {
            RespValue::Simple(_) => Ok(()),
            RespValue::Error(e) => Err(anyhow!(e)),
            other => Err(anyhow!("unexpected SET response: {:?}", other)),
        }
    }

    async fn read_value(&mut self) -> Result<RespValue> {
        loop {
            match parse_value(&self.buf)? {
                Some((val, consumed)) => {
                    let _ = self.buf.split_to(consumed);
                    return Ok(val);
                }
                None => {
                    let n = self.stream.read_buf(&mut self.buf).await?;
                    if n == 0 {
                        return Err(anyhow!("redis connection closed"));
                    }
                }
            }
        }
    }
}

fn find_crlf(buf: &[u8]) -> Option<usize> {
    buf.windows(2).position(|w| w == b"\r\n")
}

/// Returns (value, bytes_consumed) or None if incomplete.
fn parse_value(buf: &[u8]) -> Result<Option<(RespValue, usize)>> {
    if buf.is_empty() {
        return Ok(None);
    }
    match buf[0] {
        b'+' | b'-' | b':' => {
            let Some(i) = find_crlf(buf) else {
                return Ok(None);
            };
            let line = std::str::from_utf8(&buf[1..i])?;
            let val = match buf[0] {
                b'+' => RespValue::Simple(line.to_string()),
                b'-' => RespValue::Error(line.to_string()),
                b':' => RespValue::Integer(line.parse()?),
                _ => unreachable!(),
            };
            Ok(Some((val, i + 2)))
        }
        b'$' => {
            let Some(i) = find_crlf(buf) else {
                return Ok(None);
            };
            let len: i64 = std::str::from_utf8(&buf[1..i])?.parse()?;
            let header = i + 2;
            if len < 0 {
                return Ok(Some((RespValue::Bulk(None), header)));
            }
            let len = len as usize;
            if buf.len() < header + len + 2 {
                return Ok(None);
            }
            let data = std::str::from_utf8(&buf[header..header + len])?.to_string();
            Ok(Some((RespValue::Bulk(Some(data)), header + len + 2)))
        }
        b'*' => {
            let Some(i) = find_crlf(buf) else {
                return Ok(None);
            };
            let n: i64 = std::str::from_utf8(&buf[1..i])?.parse()?;
            let mut offset = i + 2;
            if n < 0 {
                return Ok(Some((RespValue::Array(vec![]), offset)));
            }
            let mut items = Vec::with_capacity(n as usize);
            for _ in 0..n {
                match parse_value(&buf[offset..])? {
                    Some((v, c)) => {
                        items.push(v);
                        offset += c;
                    }
                    None => return Ok(None),
                }
            }
            Ok(Some((RespValue::Array(items), offset)))
        }
        other => Err(anyhow!("unknown RESP type byte {}", other)),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn encode_get() {
        let b = RespClient::encode_command(&["GET", "foo"]);
        assert_eq!(b, b"*2\r\n$3\r\nGET\r\n$3\r\nfoo\r\n");
    }

    #[test]
    fn parse_bulk() {
        let raw = b"$3\r\nbar\r\n";
        let (v, n) = parse_value(raw).unwrap().unwrap();
        assert_eq!(v, RespValue::Bulk(Some("bar".into())));
        assert_eq!(n, raw.len());
    }
}
