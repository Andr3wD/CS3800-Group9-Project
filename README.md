# CS3800 Socket Project, Group 9

# Note
The server.public.pem file is specifically for the AWS EC2 instance we setup for this project.

**WARNING**: We are **not** security experts. This is just what we found through our testing, and is in no way a guaranteed secure way of going about TLS implementation.

## Changing Server Locations
If the client isn't run on the same machine as the server, the client will attempt to do hostname and cert validation.<br>
But, since the public key in this repository is signed with our AWS server FQDN, if the client attempts to connect to any server other than our AWS server, it will throw cert validation errors.

To change servers:
 1. Change the client's `ipDest` to match the server FQDN being connected to.
 2. Make new key pairs for the server. An example is [below](#Making-New-Key-Pairs). (**WARNING**: Proper key generation is reccomended for actual security. This means getting your keys from a real authority, and not just generating them yourself!)
 3. Give the server both the public and private keys, and give the client the public key.

This should fix any cert validation errors.

### Making New Key Pairs

**WARNING**: THIS IS NOT A GUARANTEED SECURE NOR PROPER WAY OF GENERATING AND TRANSFERRING KEYS. PROPER CARE SHOULD BE TAKEN WHEN HANDLING AND GENERATING KEYS.
This is just what we did to showcase our application.

This can be done using `OpenSSL` with command:
```
openssl req -x509 -newkey rsa:4096 -keyout server.private.key -out server.public.pem -nodes
```
Then go through the setup wizard and make sure to put your FQND in the FQDN location when the wizard asks for it.