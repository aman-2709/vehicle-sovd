# Placeholder TLS Certificates

These are placeholder certificate files for development. For production deployment, replace these with real certificates.

## Generating Self-Signed Certificates (Development)

For development and testing, you can generate self-signed certificates:

```bash
# Generate CA private key
openssl genrsa -out ca-key.pem 2048

# Generate CA certificate
openssl req -new -x509 -days 365 -key ca-key.pem -out ca.pem -subj "/CN=SOVD Test CA"

# Generate client private key
openssl genrsa -out client-key.pem 2048

# Generate client certificate signing request
openssl req -new -key client-key.pem -out client-csr.pem -subj "/CN=SOVD Client"

# Sign client certificate with CA
openssl x509 -req -days 365 -in client-csr.pem -CA ca.pem -CAkey ca-key.pem -CAcreateserial -out client-cert.pem

# Generate server private key
openssl genrsa -out server-key.pem 2048

# Generate server certificate signing request
openssl req -new -key server-key.pem -out server-csr.pem -subj "/CN=localhost"

# Sign server certificate with CA
openssl x509 -req -days 365 -in server-csr.pem -CA ca.pem -CAkey ca-key.pem -CAcreateserial -out server-cert.pem

# Clean up CSR files
rm client-csr.pem server-csr.pem
```

## Production Certificates

For production, obtain certificates from a trusted Certificate Authority (CA).

