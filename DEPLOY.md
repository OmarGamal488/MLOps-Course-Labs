# Deployment Guide — CI/CD to EC2

The workflow at `.github/workflows/actions.yml` runs **test → build & push → deploy**
on every push to `main`. It pulls config from GitHub *Secrets* and *Variables*.

## 1. GitHub repository configuration

Open `Settings → Secrets and variables → Actions`.

### Variables (non-sensitive — `Variables` tab)

| Name | Example | Used by |
|---|---|---|
| `DOCKERHUB_USERNAME` | `omargamal488` | build + deploy |
| `EC2_USER`           | `ubuntu`       | deploy |

### Secrets (sensitive — `Secrets` tab)

| Name | What it is |
|---|---|
| `DOCKERHUB_TOKEN`  | Docker Hub access token (Account → Security → New Access Token) |
| `EC2_HOST`         | EC2 public IPv4 or DNS, e.g. `13.51.x.x` |
| `EC2_SSH_KEY`      | Full contents of the private `.pem` key (BEGIN/END lines included) |
| `HYPERDX_API_KEY`  | (optional) HyperDX ingestion key |

## 2. EC2 instance prep (run once)

```bash
ssh -i your-key.pem ubuntu@<EC2_HOST>

# install Docker
sudo apt-get update
sudo apt-get install -y docker.io
sudo usermod -aG docker $USER
exit          # log out + back in for group to take effect
```

Security group: allow inbound TCP **80** (HTTP) and **22** (SSH) from your IP.

## 3. Docker Hub prep (run once)

1. Create a public repo `<DOCKERHUB_USERNAME>/churn-api` on hub.docker.com.
2. Generate an access token (Account → Security) and save as `DOCKERHUB_TOKEN`.

## 4. Trigger the pipeline

```bash
git push origin main
```

Watch `Actions` tab. After the deploy job finishes, hit the API:

```bash
curl http://<EC2_HOST>/health
curl http://<EC2_HOST>/
curl -X POST http://<EC2_HOST>/predict \
  -H 'Content-Type: application/json' \
  -d '{"CreditScore":650,"Geography":"France","Gender":"Female","Age":40,"Tenure":3,"Balance":60000,"NumOfProducts":2,"HasCrCard":1,"IsActiveMember":1,"EstimatedSalary":50000}'
```

Swagger UI: `http://<EC2_HOST>/schema/swagger`

## 5. Switching to AWS ECR (optional)

Replace the `Login to Docker Hub` and `IMAGE_NAME` block with:

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: ${{ vars.AWS_REGION }}

- name: Login to Amazon ECR
  id: ecr
  uses: aws-actions/amazon-ecr-login@v2
```

Then set `IMAGE_NAME: ${{ steps.ecr.outputs.registry }}/churn-api`.
