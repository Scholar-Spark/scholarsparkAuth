schema "auth" {
  table "users" {
    column "id" {
      type = "serial"
      primary_key = true
    }
    column "email" {
      type = "varchar(255)"
      unique = true
      not_null = true
    }
    column "hashed_password" {
      type = "varchar(255)"
      not_null = true
    }
    column "is_active" {
      type = "boolean"
      default = "true"
    }
    column "created_at" {
      type = "timestamp with time zone"
      default = "CURRENT_TIMESTAMP"
    }
  }
} 