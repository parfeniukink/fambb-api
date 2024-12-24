set -e

cd /home/home/fambb/fambb_backend
git pull origin main

# make sure that sudoers file is updated
# home ALL=(ALL) NOPASSWD: /bin/systemctl restart fambb_api.service
sudo systemctl restart fambb_api.service

echo "Deployed 🚀"
