# INFRA

## aws s3 backend

```
terraform init
AWS_PROFILE=wce terraform plan
AWS_PROFILE=wce terraform apply
```

## get aws credentials for deploying dev, prod, etc

```
terraform -chdir=terraform/tfbackend output -raw access_key
terraform -chdir=terraform/tfbackend output -raw secret_key
```

Create/modify these to the `[presis]` profile of `~/.aws/config`:

```
ACCESS_KEY=$(terraform -chdir=terraform/tfbackend output -raw access_key)
SECRET_KEY=$(terraform -chdir=terraform/tfbackend output -raw secret_key)
echo "
[profile presis]
aws_access_key_id = ${ACCESS_KEY}
aws_secret_access_key = ${SECRET_KEY}
region = us-east-2
" >> ~/.aws/config
```