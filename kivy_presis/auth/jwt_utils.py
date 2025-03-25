import jwt
import datetime

class JwtUtils:
    SECRET_KEY = "mysecretkey"

    @staticmethod
    def encode_token(user_id, project, scope="readonly", expires_in=24):
        """Generate a JWT token containing user ID, project, and scope."""
        exp = datetime.datetime.utcnow() + datetime.timedelta(hours=expires_in)
        return jwt.encode(
            {"user_id": user_id, "project": project, "scope": scope, "exp": exp},
            JwtUtils.SECRET_KEY,
            algorithm="HS256"
        )

    @staticmethod
    def decode_token(token):
        """Decode the JWT token to retrieve user ID and project details."""
        try:
            payload = jwt.decode(token, JwtUtils.SECRET_KEY, algorithms=["HS256"])
            return {
                "user_id": payload["user_id"],
                "project": payload["project"],
                "scope": payload["scope"]
            }
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
