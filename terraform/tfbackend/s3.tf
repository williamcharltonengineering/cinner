provider "aws" {
  region = "us-east-2"
}

module "s3_bucket" {
  source = "terraform-aws-modules/s3-bucket/aws"

  bucket = "presis-terraform-deployment-state"
  acl    = "private"

  control_object_ownership = true
  object_ownership         = "ObjectWriter"

  versioning = {
    enabled = true
  }
}

resource "aws_dynamodb_table" "dynamodb_terraform_state_lock" {
  name           = "presis-terraform-state-lock"
  read_capacity  = 20
  write_capacity = 20
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}
resource "aws_iam_user" "presis_infra_user" {
  name = "presis-infra-user"
  path = "/presis/"
}

resource "aws_iam_access_key" "presis_infra_user_key" {
  user = aws_iam_user.presis_infra_user.name
}

resource "aws_iam_user_policy" "presis_infra_user_policy" {
  name = "presis_s3_infra_user_policy"
  user = aws_iam_user.presis_infra_user.name

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Effect": "Allow",
      "Resource": [
        "${module.s3_bucket.s3_bucket_arn}",
        "${module.s3_bucket.s3_bucket_arn}/*"
      ]
    },
    {
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem",
        "dynamodb:DescribeTable",
        "dynamodb:Scan"
      ],
      "Effect": "Allow",
      "Resource": "${aws_dynamodb_table.dynamodb_terraform_state_lock.arn}"
    }
  ]
}
EOF
}
output "access_key" {
  value     = aws_iam_access_key.presis_infra_user_key.id
  sensitive = true
}

output "secret_key" {
  value     = aws_iam_access_key.presis_infra_user_key.secret
  sensitive = true
}