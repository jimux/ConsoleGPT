#!/bin/bash

# Define package name and version
PACKAGE_NAME="alpaca-web"
PACKAGE_VERSION="1.0"
SERVICE_USER="alpaca"

# Create the package directory and navigate to it
mkdir -p "${PACKAGE_NAME}-${PACKAGE_VERSION}"
cd "${PACKAGE_NAME}-${PACKAGE_VERSION}"

# Copy the Flask application (e.g., app.py) and any other necessary files
# into the package directory. Adjust the source paths as needed.
cp ../${PACKAGE_NAME}.py .

# Copy the requirements.txt file into the package directory
cp ../requirements.txt .

# Initialize the Debian package structure
dh_make --native -p "${PACKAGE_NAME}_${PACKAGE_VERSION}" -s

# Navigate to the debian subdirectory
cd debian

# Create the systemd service unit file
cat <<EOF > "${PACKAGE_NAME}.service"
[Unit]
Description=Alpaca Web Service
After=network.target

[Service]
User=${SERVICE_USER}
Group=nogroup
CapabilityBoundingSet=CAP_DAC_OVERRIDE
WorkingDirectory=/usr/lib/${PACKAGE_NAME}
Environment="PATH=/path/to/your/venv/bin"
ExecStart=/usr/bin/python3 /usr/lib/${PACKAGE_NAME}/${PACKAGE_NAME}.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Create the install file to specify the installation paths
# Include the requirements.txt file in the installation paths
cat <<EOF > "${PACKAGE_NAME}.install"
app.py /usr/lib/${PACKAGE_NAME}/
requirements.txt /usr/lib/${PACKAGE_NAME}/
debian/${PACKAGE_NAME}.service /lib/systemd/system/
EOF

# Create the postinst script to install Python dependencies
# and create the service user
cat <<EOF > postinst
#!/bin/sh

# Create the service user if it does not exist
if ! id -u ${SERVICE_USER} >/dev/null 2>&1; then
  useradd -r -s /bin/false ${SERVICE_USER}
fi

# Install Python dependencies from the requirements.txt file
/usr/bin/pip3 install -r /usr/lib/${PACKAGE_NAME}/requirements.txt

# Create the log file and set ownership and permissions
touch /var/log/${PACKAGE_NAME}.log
chown ${SERVICE_USER}:nogroup /var/log/${PACKAGE_NAME}.log
chmod 640 /var/log/${PACKAGE_NAME}.log

# Reload the systemd daemon to recognize the new service
systemctl daemon-reload

# Enable the service to start automatically at system boot
systemctl enable ${PACKAGE_NAME}.service

# Exit without errors
exit 0
EOF

# Make the postinst script executable
chmod +x postinst

# Go back to the package root directory
cd ..

# Build the .deb package
debuild -us -uc

# Print the location of the generated .deb package
echo "The .deb package has been generated in the parent directory."
