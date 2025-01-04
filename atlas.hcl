env "local" {
  url = "postgresql://user:password@db:5432/auth?sslmode=disable"

  migration {
    dir = "file://app/migrations"
  }
}

env "docker" {
  url = "postgresql://user:password@db:5432/auth?sslmode=disable"

  migration {
    dir = "file://app/migrations"
  }
}

env "kube" {
  url = "postgresql://user:password@postgres:5432/auth?sslmode=disable"

  migration {
    dir = "file://app/migrations"
  }
}