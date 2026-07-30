# EKS Kubernetes upgrade

The cluster version is centralized in the `eks_kubernetes_version` variable
(`infra/terraform/eks.tf`), threaded to the edge clusters via `edges.tf` →
`modules/edge` (`kubernetes_version`). Default target: **1.36**.

## Why now

EKS gives 14 months of standard support, then 12 months of (paid) extended support.

| Version | End of standard | End of extended |
|---------|-----------------|-----------------|
| 1.31 (previous pin) | 2025-11-26 | **2026-11-26** |
| 1.36 (new default)  | 2027-08-02 | 2028-08-02 |

1.31 has been in extended support since Nov 2025 and is **auto-upgraded after
2026-11-26**. Move to 1.36 before then to stay on standard support and avoid the
forced upgrade + extended-support cost.

## New clusters

`terraform apply` with the default creates the cluster directly at 1.36. Nothing else to do.

## Existing (live) clusters — upgrade one minor at a time

EKS does **not** allow skipping minor versions on a running cluster. From 1.31 you must
step 1.31 → 1.32 → 1.33 → 1.34 → 1.35 → 1.36. For each step:

1. Set the version and apply the control-plane bump:
   ```bash
   terraform apply -var 'eks_kubernetes_version=1.32'   # then 1.33, 1.34, 1.35, 1.36
   ```
2. Upgrade the managed node group to match (rolls nodes). This module lets the node
   group follow the cluster version; `terraform apply` handles it, or force a rollout:
   ```bash
   aws eks update-nodegroup-version --cluster-name <name> --nodegroup-name <ng>
   ```
3. Update add-ons for the new version (vpc-cni, kube-proxy, coredns) and the AWS
   Load Balancer Controller (the NLB Services in `infra/k8s/manifests.yaml` depend on it).
4. Before each step, review the EKS version release notes for removed/changed APIs and
   run `kubectl` deprecation checks against workloads.

Do the leader cluster first, verify `api.withohm.dev` miss/hit is green, then the edges
one region at a time (see `REGION_DRAIN.md`).
