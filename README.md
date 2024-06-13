# EdgeIQ CODA Snap

Official repository for EdgeIQ CODA snap


### Example of Basic Configuration

```bash
sudo snap set coda bootstrap.unique-id=testdevice
sudo snap set coda bootstrap.company-id=machineshop
sudo snap set coda conf.mqtt.broker.host=mqtt.integration.machineshop.io
sudo snap set coda conf.mqtt.broker.passwork="encrypted-password"
```

### Change Default Settings

```bash
sudo snap set coda conf.aws.greengrass.heartbeat-port=9003
```

### See bootstrap.json

```bash
sudo snap get coda "bootstrap"
cat /var/snap/coda/common/conf/bootstrap.json
cat /var/snap/coda/common/conf/identifier.json
```

### See conf.json

```bash
sudo snap get coda "conf"
cat /var/snap/coda/common/conf/conf.json
```