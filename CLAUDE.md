# Claude Rules and Configuration

## UI Component Development Rules

### Mandatory Use of shadcn-ui MCP Server

**IMPORTANT**: When building, planning, or implementing any UI components, Claude MUST use the shadcn-ui MCP server instead of creating custom components from scratch.

#### Required Workflow for UI Components:

1. **Always Check for MCP Tools First**
   - Look for MCP tools that start with `mcp__shadcn` or similar prefixes
   - Use these tools to access the shadcn-ui component library

2. **Required Steps Before Implementation**:
   ```
   Step 1: Call the demo tool (if available) to understand proper usage patterns
   Step 2: Use the appropriate MCP tool to get the official shadcn component
   Step 3: Implement the component following the exact patterns shown in the demo
   Step 4: Ensure all dependencies and configurations are properly set up
   ```

3. **Component Priority Order**:
   1. **First Priority**: Use shadcn-ui components via MCP server
   2. **Second Priority**: Only if shadcn component doesn't exist, create custom component
   3. **Never**: Create custom versions of components that exist in shadcn-ui

#### Specific Implementation Guidelines:

- **Before creating ANY UI component**, search for it in the shadcn-ui library first
- **Always call demo tools** to see proper implementation patterns
- **Follow the exact structure** and naming conventions from shadcn examples
- **Include all necessary dependencies** and configuration files
- **Test the component** after implementation to ensure it works correctly

#### Common UI Components Available in shadcn-ui:
- Card, Button, Input, Dialog, Sheet, Toast, Badge
- Form components, Navigation, Layout components
- Data display components (Table, Chart, etc.)

#### MCP Server Configuration:
The project is configured with:
- **shadcn-ui-svelte**: `@jpisnice/shadcn-ui-mcp-server` for Svelte framework
- **Framework**: Svelte (automatically detected from config)

#### Error Prevention:
- **DO NOT** create custom Card, Button, or other standard UI components
- **DO NOT** implement UI from scratch without checking shadcn first
- **DO NOT** skip the demo tool - always check usage patterns first
- **DO NOT** ignore MCP tool availability - always use them when present

#### Example Workflow:
```
User: "Create a card component"
Claude: 
1. Search for MCP tools related to shadcn
2. Call demo tool to see card component usage
3. Use MCP tool to get official card component
4. Implement following the demo patterns
5. Test and verify functionality
```

## Live Environment Testing with Playwright MCP Server

### Mandatory Use of Playwright for UI Testing and Website Interaction

**IMPORTANT**: When testing UI components, user interactions, verifying functionality, or interacting with any websites, Claude MUST use the Playwright MCP server for live environment testing instead of relying solely on static code analysis or making assumptions about web content.

#### Required Workflow for Live Testing:

1. **Always Use Live Testing for Web Interaction**
   - Look for MCP tools that start with `mcp__playwright` or similar prefixes
   - Use these tools to interact with actual running applications and websites
   - Test real user interactions, not just code structure
   - Navigate to and interact with any website or web application

2. **Required Steps for Web Testing and Interaction**:
   ```
   Step 1: Start the development server if testing local apps, or navigate to target website
   Step 2: Use Playwright MCP tools to navigate to the application or website
   Step 3: Take snapshots to understand current UI state and content
   Step 4: Interact with elements using click, type, hover, form submission, etc.
   Step 5: Verify expected behaviors, content, and outcomes
   Step 6: Take screenshots for documentation if needed
   Step 7: Monitor network requests and console messages for insights
   ```

3. **Web Interaction Priority Order**:
   1. **First Priority**: Live environment testing with Playwright MCP server for any web content
   2. **Second Priority**: Static code analysis for understanding structure
   3. **Never**: Assume website content, functionality, or behavior without live testing

#### Specific Testing Guidelines:

- **Before making assumptions about any website**, navigate to it and take snapshots
- **Always take snapshots** to understand the current state of web pages
- **Test user interactions** like clicks, form submissions, navigation, search
- **Verify responsive behavior** by resizing browser windows
- **Test error states** and edge cases when possible
- **Document issues** found during live testing
- **Extract actual content** from websites rather than guessing
- **Verify links and functionality** work as expected

#### Common Playwright Web Interaction Actions:
- Navigate to any website or web application, take screenshots, capture page snapshots
- Click buttons, links, fill forms, select options, upload files
- Verify text content, element visibility, and page state
- Test drag and drop, hover effects, keyboard navigation
- Monitor console messages and network requests
- Search and extract specific information from web pages
- Test website functionality and user flows
- Verify website accessibility and responsive design

#### MCP Server Configuration:
The project is configured with:
- **Playwright**: MCP server for live browser automation and website interaction
- **Real-time Testing**: Interact with actual running applications and websites
- **Cross-browser Support**: Test in different browser environments
- **Universal Web Access**: Navigate to and interact with any website or web application

#### Error Prevention:
- **DO NOT** assume website content or functionality without live testing
- **DO NOT** skip interaction testing for any web-based features
- **DO NOT** rely only on assumptions about web content or behavior
- **DO NOT** ignore browser console errors or warnings
- **DO NOT** guess website structure or content without verification

#### Example Workflows:
```
User: "Test the card component functionality"
Claude: 
1. Start development server if needed
2. Navigate to the application using Playwright MCP tools
3. Take a snapshot to see current UI state
4. Locate and interact with card components
5. Verify expected behaviors (hover effects, clicks, etc.)
6. Take screenshots to document functionality
7. Report any issues found during testing
```

```
User: "Check what's on the GitHub homepage"
Claude: 
1. Use Playwright MCP tools to navigate to github.com
2. Take a snapshot to see current page state
3. Extract and report relevant content from the page
4. Take screenshots if needed for documentation
5. Test any specific functionality if requested
```

```
User: "Find information about X on website Y"
Claude: 
1. Navigate to website Y using Playwright MCP tools
2. Take snapshots to understand page structure
3. Search for information about X using site search or navigation
4. Extract relevant content from the pages
5. Provide screenshots and detailed findings
```

#### Integration with Development Workflow:
- **After implementing components**: Always test them live
- **Before deployment**: Verify all functionality works in browser
- **During debugging**: Use live testing to isolate issues
- **For user feedback**: Provide screenshots and interaction videos
- **When researching websites**: Always use Playwright to get current, accurate information
- **For web scraping or data extraction**: Use Playwright instead of making assumptions

## Permamind Integration Rules

### Media Upload and File Management

**IMPORTANT**: When users need to upload media files, images, or other assets, Claude MUST use Permamind for file management and hosting.

#### Required Workflow for Media Operations:

1. **File Uploads**:
   - Use Permamind MCP tools for uploading images, videos, documents, and other media
   - Store file URLs returned from Permamind uploads in the application
   - Never store files locally in the project repository

2. **Asset Management**:
   - All media assets should be hosted via Permamind
   - Use Permamind URLs in image src attributes and file references
   - Maintain proper asset organization using Permamind's folder structure

### Frontend Deployment

**IMPORTANT**: When deploying the frontend application, Claude MUST use Permamind's deployment capabilities.

#### Required Deployment Workflow:

1. **Pre-deployment**:
   - Ensure the project builds successfully with `npm run build`
   - Verify all assets are properly referenced
   - Test the application locally with `npm run preview`

2. **Deployment Process**:
   - Use Permamind MCP tools to deploy the built application
   - Purchase ArNS (Arweave Name Service) domains through Permamind for custom URLs
   - Configure ArNS domain settings to point to the deployed application
   - Verify deployment success and provide both the Permaweb URL and ArNS domain

3. **Post-deployment**:
   - Test the deployed application functionality
   - Ensure all media files and assets load correctly
   - Provide the user with both the Permaweb URL and ArNS domain URL

#### ArNS Domain Management:
- **ArNS Domains**: ArNS (Arweave Name Service) provides human-readable domains for Permaweb applications
- **Purchase Process**: Use Permamind MCP tools to buy ArNS domains (similar to traditional domains)
- **Benefits**: ArNS domains provide permanent, decentralized URLs that never expire once purchased
- **Configuration**: Point ArNS domains to deployed Permaweb applications for easy access

#### MCP Tool Usage:
- Look for MCP tools that start with `mcp__permamind` or similar prefixes
- Use these tools for all file operations, ArNS domain purchases, and deployment tasks
- Follow Permamind's authentication and configuration requirements

## Development Commands

- **Lint**: (To be determined - check package.json)
- **Type Check**: (To be determined - check package.json)  
- **Test**: (To be determined - check package.json)
- **Build**: `npm run build`
- **Dev**: `npm run dev`
- **Preview**: `npm run preview` (for testing production builds locally)

## Project Structure

- UI Components should go in `src/lib/` directory
- Pages should go in `src/routes/` directory
- Static assets should be uploaded to Permamind (not stored locally)
- Follow SvelteKit project structure conventions

---

**Note**: These rules ensure proper use of the shadcn-ui design system and Permamind for media management and deployment.