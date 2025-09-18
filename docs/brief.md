# Project Brief: RNG Miner Onboarding System

## Executive Summary

**Project Concept:** A comprehensive IoT device onboarding platform consisting of cross-platform mobile applications (Android/iOS) and embedded software for OrangePi Zero W3 devices that solves the "first mile problem" in IoT deployment by automating WiFi configuration and initial device setup.

**Primary Problem Being Solved:** IoT devices face a critical deployment barrier where end users struggle to configure WiFi credentials and perform initial setup, creating friction between manufacturing and successful field deployment.

**Target Market:** Mainstream crypto mining customers seeking passive income opportunities without technical complexity barriers.

**Key Value Proposition:** Eliminate the technical complexity of IoT device onboarding through automated WiFi detection, guided mobile app configuration, and standardized BIP32 credential management, transforming a typically complex technical process into a consumer-friendly experience.

## Problem Statement

**Current State:** Crypto mining devices face a critical deployment barrier where non-technical mainstream consumers struggle with the initial setup process. Traditional IoT devices require users to manually configure WiFi credentials and cryptographic keys through command line interfaces, web dashboards, or complex mobile apps that assume technical expertise.

**Specific Pain Points:**
- **Technical Complexity**: Users must navigate SSH connections, configuration files, and command-line tools to set up WiFi and BIP32 phrases
- **Setup Friction**: The gap between "device powered on" and "device mining" creates abandonment and support burden
- **Network Configuration**: Home users struggle with finding device IP addresses, accessing web interfaces, and troubleshooting connection issues
- **Security vs Usability**: Secure key management typically requires technical knowledge that mainstream users lack
- **Field Deployment Challenges**: Devices configured in production facilities lose connectivity when moved to user locations, requiring complex reconfiguration

**Impact Quantification:**
- Estimated 60-80% of mainstream users abandon technical setup processes
- Support costs increase significantly with complex onboarding procedures
- Time-to-mining delays reduce user satisfaction and device utilization
- Manual configuration creates scaling bottlenecks for device manufacturing

**Why Existing Solutions Fall Short:**
- Generic IoT setup solutions don't address crypto-specific requirements (BIP32 key management)
- Enterprise IoT platforms are over-engineered and expensive for consumer crypto mining devices
- Web-based configuration requires users to find device IP addresses and navigate unfamiliar interfaces
- Command-line setup creates insurmountable barriers for mainstream adoption

**Urgency:** With plans to manufacture 1,000 units, a streamlined onboarding solution is essential to ensure successful customer deployment and minimize support overhead.

## Proposed Solution

**Core Concept:** A dual-component onboarding platform consisting of embedded software for OrangePi Zero W3 devices and a cross-platform mobile application that eliminates technical complexity through automated device discovery, guided WiFi configuration, and secure BIP32 key management.

**Two-Repository Architecture:**
- **Device Install Script Repository**: Automated installation package that configures OrangePi devices with fallback access point capabilities, REST API endpoints, and mining software integration
- **Mobile Application Repository**: React Native app (extending existing RNG-APP framework) that discovers devices, guides users through setup, and provides ongoing device management

**Solution Flow:**
1. **Manufacturing Phase**: Devices receive base installation script during production, creating a standardized, ready-to-deploy state
2. **Deployment Detection**: Device boots and automatically detects WiFi connectivity status using systematic network interface monitoring
3. **Fallback Mode**: If unconfigured or disconnected, device launches "RNG-Miner-XXX" access point (192.168.4.1/24) and broadcasts configuration endpoints
4. **User-Guided Setup**: Mobile app scans for both access points and network-connected devices, connecting users to the nearest setup mode device
5. **Streamlined Configuration**: App collects WiFi credentials and BIP32 phrase through intuitive UI, then transmits securely to device via REST APIs
6. **Automated Deployment**: Device connects to target network, clones mining repository, initializes Docker environment with provided BIP32 wallet, and begins mining operations
7. **Ongoing Management**: App discovers configured devices on home networks and provides remote management capabilities including software updates and system monitoring

**Key Differentiators:**
- **Zero Technical Knowledge Required**: Complete setup through familiar mobile app interface without command-line access or web browser navigation
- **Automatic Fallback Recovery**: Devices self-recover from network changes by reverting to setup mode, eliminating manual factory reset procedures
- **Integrated Crypto Management**: Native BIP32 phrase handling designed specifically for crypto mining workflows rather than generic IoT applications
- **Dual-Mode Discovery**: App intelligently handles both initial setup (AP mode) and ongoing management (network mode) through unified interface

**Why This Succeeds Where Others Fail:**
- Addresses crypto-specific requirements (BIP32) that generic IoT platforms ignore
- Eliminates IP address discovery and web interface navigation barriers
- Provides automatic recovery mechanisms for non-technical users
- Leverages familiar mobile interaction patterns instead of technical interfaces

## Target Users

### Primary User Segment: Mainstream Crypto Mining Customers

**Demographic Profile:**
- Age: 25-45 years old
- Income: Middle to upper-middle class ($50K-$150K annually)
- Technical comfort: Basic smartphone/app usage, limited technical troubleshooting abilities
- Crypto experience: Interested in mining but intimidated by technical setup requirements
- Location: Home users with standard residential WiFi networks

**Current Behaviors & Workflows:**
- Research crypto mining opportunities through social media, YouTube, and online communities
- Expect consumer electronics setup experience (plug-in, download app, follow guided setup)
- Abandon products requiring command-line interface or complex configuration
- Seek "passive income" opportunities with minimal ongoing maintenance
- Rely on mobile apps for device management rather than web interfaces

**Specific Needs & Pain Points:**
- **Setup Anxiety**: Fear of "breaking" expensive devices through incorrect configuration
- **Technical Overwhelm**: Network configuration, SSH access, and key management create barriers
- **Trust Issues**: Uncertainty about secure handling of crypto wallet keys during setup
- **Time Constraints**: Want quick, straightforward setup process that doesn't require learning new technical skills
- **Support Expectations**: Expect responsive support when issues arise, but prefer self-service solutions

**Goals They're Trying to Achieve:**
- Generate passive crypto income with minimal technical involvement
- Set up mining device quickly and confidently without technical knowledge
- Monitor device performance and earnings through simple, mobile-friendly interface
- Easily recover from common issues (WiFi changes, device relocation) without support calls
- Feel confident that their crypto assets and personal network remain secure

### Secondary User Segment: Tech-Curious Early Adopters

**Demographic Profile:**
- Age: 20-35 years old
- Technical comfort: Above average, but still prefer streamlined experiences
- Crypto experience: More experienced with crypto concepts, may run multiple mining setups
- Deployment context: May set up devices for friends/family or manage small fleets

**Specific Needs:**
- Quick bulk setup capabilities for managing multiple devices
- Advanced monitoring and troubleshooting access when needed
- Ability to customize configurations beyond standard setup
- Documentation for extending functionality or integrating with existing systems

## Goals & Success Metrics

### Business Objectives
- **Successful device deployment rate ≥95%**: Ensure that 950+ of 1,000 manufactured devices successfully complete initial setup and begin mining within 72 hours of user activation
- **Setup abandonment rate <10%**: Less than 100 users abandon the setup process before completing WiFi and BIP32 configuration
- **Support ticket reduction target of 80%**: Reduce anticipated technical support requests from estimated 400+ tickets (without guided setup) to <80 tickets for 1,000 device deployments
- **Average setup time ≤15 minutes**: Complete user journey from device unboxing to active mining status within 15 minutes for 90% of users
- **Manufacturing scalability validation**: Demonstrate that installation script and device imaging process can reliably prepare devices at production scale without manual intervention

### User Success Metrics
- **First-time setup success rate ≥90%**: Users complete entire setup flow without requiring support intervention or multiple attempts
- **WiFi configuration accuracy ≥98%**: Devices successfully connect to user-specified networks on first attempt after credential input
- **BIP32 key acceptance rate 100%**: All valid 12-word phrases are correctly processed and integrated into mining operation
- **User confidence score ≥4.2/5.0**: Post-setup survey indicates users feel confident about device security and operation (measured after 1 week of operation)
- **Recovery success rate ≥85%**: Users successfully reconfigure devices after network changes (WiFi password updates, location moves) without support assistance

### Key Performance Indicators (KPIs)
- **Device Online Rate**: ≥95% of successfully configured devices remain connected and mining 30 days post-setup
- **App Store Rating**: Maintain ≥4.0 star rating across iOS and Android app stores throughout 1K device rollout
- **Setup Error Rate**: <5% of setup attempts result in technical errors requiring app restart or device factory reset
- **Network Connectivity Success**: ≥98% of devices successfully transition from setup AP mode to home network connectivity
- **Mining Initialization Time**: ≥90% of devices begin mining operations within 10 minutes of completing network connectivity
- **Support Cost Per Device**: <$5 average support cost per device for the entire 1K unit production run
- **Feature Utilization**: ≥70% of users successfully use post-setup device management features (status checking, basic troubleshooting) within first month

## MVP Scope

### Core Features (Must Have)

- **Device Installation Script**: Automated installation package that configures OrangePi Zero W3 with systemd services for network monitoring, access point management, and REST API endpoints. Script must handle fresh Armbian installations and create all necessary configuration files in `/root/rng-config/` directory.

- **Automatic Network State Detection**: Service continuously monitors WiFi connectivity and automatically switches between operational mode (connected to home network) and setup mode (broadcasting "RNG-Miner-XXX" access point on 192.168.4.1/24 network).

- **Mobile Device Discovery**: React Native app (built from RNG-APP template) scans for both access points matching "RNG-Miner-" pattern and network-connected devices broadcasting on standardized ports, providing unified interface for device detection regardless of connection state.

- **Guided WiFi Configuration**: Mobile app collects home WiFi SSID and password through intuitive interface, validates credentials format, and securely transmits to device via REST API. Device updates wpa_supplicant configuration and attempts connection with automatic fallback to setup mode on failure.

- **BIP32 Key Management**: App provides secure input interface for 12-word BIP32 phrases with validation and confirmation steps. Device stores phrase in root-only accessible file (`/root/rng-config/wallet.key`) and passes to Randomness-Provider repository during mining initialization.

- **Mining Software Integration**: Device automatically clones https://github.com/RandAOLabs/Randomness-Provider.git, configures Docker environment with provided BIP32 phrase, and initiates mining operation with systemd service management and automatic restart capabilities.

- **Basic Device Status API**: REST endpoints provide device state information including network connectivity, mining status, system resources (CPU, memory, disk), and configuration status accessible to mobile app for monitoring and troubleshooting.

- **Factory Reset Capability**: Both app-initiated and device-side factory reset functionality that clears WiFi credentials, BIP32 keys, stops mining services, and returns device to unconfigured setup mode for redeployment or troubleshooting.

### Out of Scope for MVP

- Advanced device management and monitoring dashboards
- Bulk device provisioning and fleet management tools
- Cloud-based device registry and remote management
- Detailed mining performance analytics and reporting
- Over-the-air firmware updates and automated patching
- Multi-network support or enterprise WiFi configurations
- Advanced security features (certificate management, encrypted storage)
- User account management and device ownership tracking
- Integration with external mining pools or services
- Custom hardware enclosures or industrial design
- Detailed documentation and user manuals

### MVP Success Criteria

**Technical Success**: Device successfully transitions from unconfigured state to active mining within 15 minutes of user interaction, maintains stable operation for 30+ days, and recovers automatically from common network disruptions without user intervention.

**User Experience Success**: 90%+ of mainstream users complete setup process without technical support, express confidence in device security, and successfully use basic troubleshooting features when network issues occur.

**Business Validation**: Manufacturing and deployment process scales successfully to 1,000 units with <5% failure rate and <$5 average support cost per device, providing foundation for expanded production and enhanced feature development.

## Post-MVP Vision

### Phase 2 Features
**Enhanced Security Framework**: Implementation of device certificates, encrypted storage for BIP32 phrases, and secure communication channels for all device-app interactions.

**Over-the-Air Updates**: Automated software updates, mining repository updates, and system patches deployable through mobile app without requiring physical device access.

**Fleet Management for Power Users**: Basic multi-device management capabilities for users managing multiple devices across different locations.

### Long-term Vision
Transform the platform into a **comprehensive crypto mining device ecosystem** that extends beyond initial onboarding to provide complete lifecycle management. Vision includes integration with multiple mining protocols, support for different hardware platforms beyond OrangePi, and development of a marketplace for mining device configurations and optimizations.

**Ecosystem Expansion**: Support for additional crypto mining algorithms, integration with popular mining pools, and development partnerships with other hardware manufacturers to standardize the onboarding experience across different device types.

**Community Features**: User forums, mining performance leaderboards, and shared configuration libraries that enable users to optimize their devices based on community knowledge and best practices.

### Expansion Opportunities
**Enterprise IoT Onboarding Platform**: Generalize the core technology to support non-mining IoT devices, potentially licensing the onboarding framework to other manufacturers facing similar "first mile" deployment challenges.

**Hardware Integration Services**: Offer complete manufacturing integration services to crypto projects needing consumer-ready hardware deployment, expanding from internal use to B2B service offerings.

**Mining-as-a-Service Platform**: Develop hosted mining services where users purchase managed devices but benefit from professional deployment, monitoring, and optimization services.

## Technical Considerations

### Platform Requirements
- **Target Platforms:** iOS 12+ and Android 8+ (API level 26+) for mobile application
- **Device Hardware:** OrangePi Zero W3 with minimum 1GB RAM, built-in WiFi capability
- **OS Support:** Armbian (Ubuntu Noble or latest stable) with systemd service management
- **Performance Requirements:** Device must handle simultaneous AP hosting, REST API serving, and Docker container management without affecting mining performance

### Technology Preferences
- **Frontend:** React Native (extending existing RNG-APP framework) with TypeScript for type safety and Jest for testing
- **Backend:** Python Flask/FastAPI for REST API services on device, with systemd service management for reliability
- **Database:** File-based JSON configuration storage in `/root/rng-config/` directory (no database engine required for MVP)
- **Networking:** hostapd + dnsmasq for access point functionality, wpa_supplicant for WiFi client connections
- **Mining Integration:** Docker Compose integration with existing Randomness-Provider repository

### Architecture Considerations
- **Repository Structure:** Two separate repositories - device installation scripts and mobile application code, with clear API contract documentation
- **Service Architecture:** systemd services for network monitoring, access point management, API server, and mining container orchestration
- **Communication Protocol:** HTTP REST APIs with JSON payloads, no authentication (relying on network isolation), standardized error response format
- **State Management:** File-based state persistence with atomic write operations for configuration changes
- **Device Discovery:** mDNS broadcasting for network-connected devices, WiFi SSID pattern matching for setup mode devices

### API Endpoint Specifications
```
GET  /status           - Device state, network status, mining status, system metrics
POST /configure        - WiFi credentials and BIP32 phrase setup
POST /factory-reset    - Clear all configuration and return to setup mode
POST /execute-script   - Run arbitrary scripts with root permissions for updates/patches
GET  /logs            - Recent system and mining logs for troubleshooting
POST /restart-mining  - Restart mining services without full device reboot
```

### Integration Requirements
- **Mining Repository Integration:** Automated git clone of https://github.com/RandAOLabs/Randomness-Provider.git with BIP32 configuration injection
- **Network Management:** Seamless transitions between AP mode (192.168.4.1/24) and client mode with automatic fallback
- **Security Requirements:** BIP32 phrase storage in root-only accessible files with proper file permissions (600)
- **Testing Infrastructure:** Mock API endpoints for app development and automated testing without requiring physical devices

## Constraints & Assumptions

### Constraints
- **Budget:** MVP development must be cost-effective for 1,000 unit production run with minimal external service dependencies or licensing costs
- **Timeline:** Target 8-12 week development cycle to meet production scheduling requirements, prioritizing functional completeness over polish
- **Resources:** Single developer implementation approach requiring clear, well-documented code and straightforward deployment procedures
- **Hardware:** Limited to OrangePi Zero W3 capabilities - 1GB RAM, ARM64 architecture, single WiFi interface that must handle both AP and client modes
- **Network Environment:** Must function in typical home WiFi environments without enterprise network features, VPN conflicts, or complex firewall configurations
- **Testing Infrastructure:** Limited to manual testing with actual hardware deployment since automated testing of network configuration and device interactions is impractical

### Key Assumptions
- **User WiFi Networks:** Home networks use standard WPA2/WPA3 with simple SSID/password authentication (no enterprise certificates, captive portals, or MAC filtering)
- **Mobile Device Capabilities:** Users have smartphones capable of running React Native applications and can connect to both WiFi networks and mobile hotspots
- **Production Environment:** Manufacturing facility has reliable internet connectivity for initial device configuration and git repository access during installation script execution
- **Device Reliability:** OrangePi Zero W3 hardware provides sufficient stability for continuous operation with basic systemd service management and automatic restart capabilities
- **User Behavior:** Mainstream users will follow guided setup instructions and won't attempt manual configuration or system modifications that could interfere with automated processes
- **Network Stability:** Home WiFi networks remain relatively stable with infrequent password changes, and when changes occur, users will understand that device reconfiguration is necessary
- **BIP32 Security:** File-based storage with root permissions provides adequate security for MVP deployment, with users understanding basic security implications of their 12-word phrases
- **Development Iteration:** Testing and debugging can be effectively performed with 1-3 physical devices rather than requiring large-scale simulation or testing infrastructure

## Risks & Open Questions

### Key Risks
- **Single WiFi Interface Complexity**: OrangePi switching between AP and client modes may cause connectivity gaps or service failures
- **Network Discovery Reliability**: mDNS and WiFi scanning may fail in complex home network environments with multiple access points or mesh networks
- **BIP32 Transmission Security**: Sending crypto keys over local WiFi creates potential interception risk even with network isolation
- **Mining Service Stability**: Docker container crashes or git repository issues could leave devices non-functional without easy recovery

### Open Questions
- How long should device wait in AP mode before timing out?
- What happens if multiple devices are in setup mode simultaneously?
- Should app store multiple device configurations or discover each time?
- How to handle partial setup failures (WiFi works but BIP32 fails)?

### Areas Needing Further Research
- OrangePi Zero W3 WiFi interface switching capabilities and timing requirements
- React Native network scanning and WiFi management API limitations on iOS vs Android
- Home network interference patterns that might affect device discovery

## Next Steps

### Immediate Actions
1. **Create device installation script repository** with basic systemd service structure and API endpoints
2. **Set up mobile app development environment** using RNG-APP template with device discovery framework
3. **Implement mock API server** for parallel app development without requiring physical devices
4. **Define detailed API contract documentation** including request/response formats and error handling
5. **Create basic network state detection script** to validate OrangePi WiFi switching capabilities

### PM Handoff

This Project Brief provides complete context for the RNG Miner Onboarding System. **Ready for immediate development phase.** All core requirements, technical specifications, and success criteria are defined. The two-repository approach (device scripts + mobile app) enables parallel development with clear integration points via REST APIs.

**Key development priorities:** Start with device-side API server and network management, then mobile app device discovery, followed by configuration integration and mining automation. Testing requires physical deployment from day one.

---

🚀 **Project Brief Complete - Ready for Development Team Handoff**