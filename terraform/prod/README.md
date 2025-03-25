
## Force Release Lock
```
$ ./deploy.sh prod apply
AWS_PROFILE=wce
TF_VAR_namecheap_api_key=7217...
LINODE_TOKEN=a3c61ea086c9c82f781193736ec3ff6e9aa6ea37dbbbe5d4...
Unstaged changes detected. Please commit or stash them before deploying.
Acquiring state lock. This may take a few moments...
╷
│ Error: Error acquiring the state lock
│ 
│ Error message: ConditionalCheckFailedException: The conditional request
│ failed
│ Lock Info:
│   ID:        872fdd99-f21c-1a2b-b831-e0488b351f39
│   Path:      presis-terraform-deployment-state/presis-prod/deployments/terraform.tfstate
│   Operation: OperationTypeApply
│   Who:       will@Williams-MacBook-Pro.local
│   Version:   1.5.7
│   Created:   2024-08-11 05:01:13.086778 +0000 UTC
│   Info:      
│ 
│ 
│ Terraform acquires a state lock to protect the state from being written
│ by multiple users at the same time. Please resolve the issue above and try
│ again. For most commands, you can disable locking with the "-lock=false"
│ flag, but this is not recommended.
╵
[will@W-MB-P|00:06:45|~/williamcharltonengineering/presis](master)
$ AWS_PROFILE=presis \
    aws dynamodb \
    delete-item \
    --table-name presis-terraform-state-lock \
    --key '{"LockID": {"S": "presis-terraform-deployment-state/presis-prod/deployments/terraform.tfstate"}}'
```

## Manually Destroy Terraform State

```
AWS_PROFILE=chili \
    aws dynamodb \
    delete-item \
    --table-name lee-county-chili-challenge-2024-dynamodb-terraform-state-lock \
    --key '{"LockID": {"S": "lee-county-chili-challenge-2024-deployment-state/lee-county-chili-challenge-2024/deployments/mbp-m2/dev/terraform.tfstate"}}'
AWS_PROFILE=chili \
    aws dynamodb \
    delete-item \
    --table-name lee-county-chili-challenge-2024-dynamodb-terraform-state-lock \
    --key '{"LockID": {"S": "lee-county-chili-challenge-2024-deployment-state/lee-county-chili-challenge-2024/deployments/mbp-m2/dev/terraform.tfstate-md5"}}'

```