#! /bin/sh

sudo systemctl status irrigation.service
echo ""
sudo systemctl status irrigation_subscription.service
echo ""
sudo systemctl status manual_control.service
echo ""
sudo systemctl status manual_mode.service
echo ""
sudo systemctl status plant_mapping.service