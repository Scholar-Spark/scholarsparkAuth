DO
$$
BEGIN
   IF NOT EXISTS (
      SELECT
      FROM   pg_catalog.pg_database
      WHERE  datname = 'auth') THEN
      CREATE DATABASE auth;
   END IF;
END
$$; 