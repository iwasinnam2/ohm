FROM rust:1.87-bookworm AS build
WORKDIR /src
COPY Cargo.toml Cargo.lock ./
COPY src ./src
RUN cargo build --release --locked

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/target/release/at-gateway-rs /usr/local/bin/at-gateway-rs
ENV AT_RS_LISTEN=0.0.0.0:8081
EXPOSE 8081
CMD ["at-gateway-rs"]
