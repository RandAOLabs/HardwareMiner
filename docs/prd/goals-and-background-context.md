# Goals and Background Context

## Goals
- Enable seamless first-mile setup of Orange Pi Zero 3 IoT mining devices via mobile app
- Provide foolproof device configuration that connects IoT devices to home WiFi networks
- Automate mining software installation and startup on configured devices
- Ensure quality assurance through complete device wipe/restart capability on setup failures
- Deliver a mobile app that simplifies complex IoT provisioning into a user-friendly experience
- Create a scalable system for mass deployment of pre-configured IoT mining devices
- Enable ongoing device management and remote updates through secure app-to-device communication
- Support remote script execution capability for device maintenance and software updates

## Background Context

This PRD addresses the critical "first-mile problem" in IoT device deployment - the complex initial setup process that prevents widespread adoption of IoT mining solutions. Currently, users struggle with manually configuring network settings, installing software, and troubleshooting connectivity issues on headless devices like the Orange Pi Zero 3.

Our solution splits into two complementary components: a mobile app that handles user interaction and device discovery, and embedded software that runs on Orange Pi devices to facilitate setup communication and manage mining operations. The system assumes users have smartphone WiFi access and home network credentials, leveraging these to bridge the connectivity gap for new IoT devices. The fail-safe approach of complete device wiping ensures consistent quality and eliminates partial-configuration states that could cause support issues.

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|---------|
| 2025-09-14 | v1.0 | Initial PRD creation for IoT setup system | John (PM) |
