targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment for resource naming')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('AI Services account name (will contain the AI Project)')
param aiServicesName string = ''

@description('AI Foundry Project name')
param aiProjectName string = ''

@description('AI Search service name')
param searchServiceName string = ''

@description('Container Apps Environment name')
param containerAppsEnvName string = ''

@description('Enable AI Search service')
param enableSearch bool = true

@description('Deploy Container Apps (false for initial provision, true for azd deploy)')
param deployContainerApps bool = false

@description('Id of the user or app to assign application roles')
param principalId string = ''

@description('OpenAI model deployment name (e.g., gpt-4o, gpt-4o-mini)')
param openAiModelName string = 'gpt-4o'

@description('OpenAI model version')
param openAiModelVersion string = '2024-11-20'

@description('OpenAI model SKU capacity')
param openAiModelCapacity int = 50

// Tags for all resources
var tags = {
  'azd-env-name': environmentName
}

var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))

// Resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

// Key Vault
module keyVault './core/security/keyvault.bicep' = {
  name: 'keyvault'
  scope: rg
  params: {
    name: '${abbrs.keyVaultVaults}${resourceToken}'
    location: location
    tags: tags
    principalId: principalId
  }
}

// Storage Account
module storage './core/storage/storage-account.bicep' = {
  name: 'storage'
  scope: rg
  params: {
    name: '${abbrs.storageStorageAccounts}${resourceToken}'
    location: location
    tags: tags
  }
}

// Container Registry
module containerRegistry './core/host/container-registry.bicep' = {
  name: 'container-registry'
  scope: rg
  params: {
    name: '${abbrs.containerRegistryRegistries}${resourceToken}'
    location: location
    tags: tags
  }
}

// Application Insights
module monitoring './core/monitor/monitoring.bicep' = {
  name: 'monitoring'
  scope: rg
  params: {
    location: location
    tags: tags
    logAnalyticsName: '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    applicationInsightsName: '${abbrs.insightsComponents}${resourceToken}'
  }
}

// AI Search (optional, for RAG)
module search './core/search/ai-search.bicep' = if (enableSearch) {
  name: 'ai-search'
  scope: rg
  params: {
    name: !empty(searchServiceName) ? searchServiceName : 'srch-${resourceToken}'
    location: location
    tags: tags
    sku: {
      name: 'basic'
    }
  }
}

// AI Foundry Project (includes AI Services account + Project + Connections)
module aiFoundry './core/ai/ai-project.bicep' = {
  name: 'ai-foundry-project'
  scope: rg
  params: {
    location: location
    tags: tags
    aiServiceName: !empty(aiServicesName) ? aiServicesName : 'aoai-${resourceToken}'
    aiProjectName: !empty(aiProjectName) ? aiProjectName : 'proj-${resourceToken}'
    storageAccountId: storage.outputs.id
    storageAccountTarget: storage.outputs.primaryEndpoints.blob
    appInsightsId: monitoring.outputs.applicationInsightsId
    appInsightConnectionString: monitoring.outputs.applicationInsightsConnectionString
    appInsightConnectionName: 'appinsights-connection'
    aoaiConnectionName: 'aoai-connection'
    storageAccountConnectionName: 'storage-connection'
    deployments: [
      {
        name: openAiModelName
        model: {
          format: 'OpenAI'
          name: openAiModelName
          version: openAiModelVersion
        }
        sku: {
          name: 'GlobalStandard'
          capacity: openAiModelCapacity
        }
      }
      {
        name: 'text-embedding-3-large'
        model: {
          format: 'OpenAI'
          name: 'text-embedding-3-large'
          version: '1'
        }
        sku: {
          name: 'Standard'
          capacity: 50
        }
      }
    ]
  }
}

// Role assignments for AI Foundry Project
module cognitiveServicesUserRole './core/security/role.bicep' = if (!empty(principalId)) {
  name: 'cognitive-services-user-role'
  scope: rg
  params: {
    principalId: principalId
    roleDefinitionId: 'a97b65f3-24c7-4388-baec-2e87135dc908' // Cognitive Services User
    principalType: 'User'
  }
}

module azureAIUserRole './core/security/role.bicep' = if (!empty(principalId)) {
  name: 'azure-ai-user-role'
  scope: rg
  params: {
    principalId: principalId
    roleDefinitionId: '53ca6127-db72-4b80-b1b0-d745d6d5456d' // Azure AI User
    principalType: 'User'
  }
}

module storageBlobDataContributorRole './core/security/role.bicep' = if (!empty(principalId)) {
  name: 'storage-blob-data-contributor-role'
  scope: rg
  params: {
    principalId: principalId
    roleDefinitionId: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe' // Storage Blob Data Contributor
    principalType: 'User'
  }
}

// Container Apps Environment
module containerAppsEnv './core/host/container-apps-environment.bicep' = {
  name: 'container-apps-env'
  scope: rg
  params: {
    name: !empty(containerAppsEnvName) ? containerAppsEnvName : '${abbrs.appManagedEnvironments}${resourceToken}'
    location: location
    tags: tags
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
  }
}

// Common environment variables for all agents
var commonEnvVars = [
  {
    name: 'AZURE_AI_PROJECT_CONNECTION_STRING'
    value: '${aiFoundry.outputs.projectEndpoint};subscription_id=${subscription().subscriptionId};resource_group=${rg.name}'
  }
  {
    name: 'AZURE_OPENAI_ENDPOINT'
    value: aiFoundry.outputs.endpoint
  }
  {
    name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
    value: monitoring.outputs.applicationInsightsConnectionString
  }
]

// Container Apps - Main Agent
module agentMain './core/host/container-app.bicep' = if (deployContainerApps) {
  name: 'agent-main'
  scope: rg
  params: {
    name: '${abbrs.appContainerApps}main-${resourceToken}'
    location: location
    tags: tags
    serviceName: 'agent-main'
    environmentId: containerAppsEnv.outputs.id
    containerRegistryName: containerRegistry.outputs.name
    imageName: 'mcr.microsoft.com/k8se/quickstart:latest' // Placeholder - will be updated by azd deploy
    cpu: '1.0'
    memory: '2Gi'
    targetPort: 8000
    external: true
    environmentVariables: concat(commonEnvVars, [
      {
        name: 'AGENT_TYPE'
        value: 'main'
      }
    ])
  }
}

// Container Apps - Researcher Agent
module agentResearcher './core/host/container-app.bicep' = if (deployContainerApps) {
  name: 'agent-researcher'
  scope: rg
  params: {
    name: '${abbrs.appContainerApps}researcher-${resourceToken}'
    location: location
    tags: tags
    serviceName: 'agent-researcher'
    environmentId: containerAppsEnv.outputs.id
    containerRegistryName: containerRegistry.outputs.name
    imageName: 'mcr.microsoft.com/k8se/quickstart:latest' // Placeholder
    cpu: '0.5'
    memory: '1Gi'
    targetPort: 8000
    external: false
    environmentVariables: concat(commonEnvVars, [
      {
        name: 'AGENT_TYPE'
        value: 'researcher'
      }
    ])
  }
}

// Container Apps - Writer Agent
module agentWriter './core/host/container-app.bicep' = if (deployContainerApps) {
  name: 'agent-writer'
  scope: rg
  params: {
    name: '${abbrs.appContainerApps}writer-${resourceToken}'
    location: location
    tags: tags
    serviceName: 'agent-writer'
    environmentId: containerAppsEnv.outputs.id
    containerRegistryName: containerRegistry.outputs.name
    imageName: 'mcr.microsoft.com/k8se/quickstart:latest' // Placeholder
    cpu: '0.5'
    memory: '1Gi'
    targetPort: 8000
    external: false
    environmentVariables: concat(commonEnvVars, [
      {
        name: 'AGENT_TYPE'
        value: 'writer'
      }
    ])
  }
}

// Container Apps - MCP Server
module mcpServer './core/host/container-app.bicep' = if (deployContainerApps) {
  name: 'mcp-server'
  scope: rg
  params: {
    name: '${abbrs.appContainerApps}mcp-${resourceToken}'
    location: location
    tags: tags
    serviceName: 'mcp-server'
    environmentId: containerAppsEnv.outputs.id
    containerRegistryName: containerRegistry.outputs.name
    imageName: 'mcr.microsoft.com/k8se/quickstart:latest' // Placeholder
    cpu: '0.5'
    memory: '1Gi'
    targetPort: 8000
    external: false
    environmentVariables: commonEnvVars
  }
}

// Container Apps - Evaluator
module evaluator './core/host/container-app.bicep' = if (deployContainerApps) {
  name: 'evaluator'
  scope: rg
  params: {
    name: '${abbrs.appContainerApps}eval-${resourceToken}'
    location: location
    tags: tags
    serviceName: 'evaluator'
    environmentId: containerAppsEnv.outputs.id
    containerRegistryName: containerRegistry.outputs.name
    imageName: 'mcr.microsoft.com/k8se/quickstart:latest' // Placeholder
    cpu: '0.5'
    memory: '1Gi'
    targetPort: 8000
    external: false
    environmentVariables: commonEnvVars
  }
}

// Grant Container Apps access to AI Services
module agentMainAIRole './core/security/role.bicep' = if (deployContainerApps) {
  name: 'agent-main-ai-role'
  scope: rg
  params: {
    principalId: agentMain!.outputs.identityPrincipalId
    roleDefinitionId: '53ca6127-db72-4b80-b1b0-d745d6d5456d' // Azure AI User (required for agents/write)
    principalType: 'ServicePrincipal'
  }
}

module agentMainAIUserRole './core/security/role.bicep' = if (deployContainerApps) {
  name: 'agent-main-ai-user-role'
  scope: rg
  params: {
    principalId: agentMain!.outputs.identityPrincipalId
    roleDefinitionId: 'a97b65f3-24c7-4388-baec-2e87135dc908' // Cognitive Services User (required for model inference)
    principalType: 'ServicePrincipal'
  }
}

module agentResearcherAIRole './core/security/role.bicep' = if (deployContainerApps) {
  name: 'agent-researcher-ai-role'
  scope: rg
  params: {
    principalId: agentResearcher!.outputs.identityPrincipalId
    roleDefinitionId: '53ca6127-db72-4b80-b1b0-d745d6d5456d' // Azure AI User
    principalType: 'ServicePrincipal'
  }
}

module agentResearcherAIUserRole './core/security/role.bicep' = if (deployContainerApps) {
  name: 'agent-researcher-ai-user-role'
  scope: rg
  params: {
    principalId: agentResearcher!.outputs.identityPrincipalId
    roleDefinitionId: 'a97b65f3-24c7-4388-baec-2e87135dc908' // Cognitive Services User
    principalType: 'ServicePrincipal'
  }
}

module agentWriterAIRole './core/security/role.bicep' = if (deployContainerApps) {
  name: 'agent-writer-ai-role'
  scope: rg
  params: {
    principalId: agentWriter!.outputs.identityPrincipalId
    roleDefinitionId: '53ca6127-db72-4b80-b1b0-d745d6d5456d' // Azure AI User
    principalType: 'ServicePrincipal'
  }
}

module agentWriterAIUserRole './core/security/role.bicep' = if (deployContainerApps) {
  name: 'agent-writer-ai-user-role'
  scope: rg
  params: {
    principalId: agentWriter!.outputs.identityPrincipalId
    roleDefinitionId: 'a97b65f3-24c7-4388-baec-2e87135dc908' // Cognitive Services User
    principalType: 'ServicePrincipal'
  }
}

// Outputs - Minimized to essential variables only
// Core Azure context
output AZURE_RESOURCE_GROUP string = rg.name
output AZURE_LOCATION string = location
output AZURE_SUBSCRIPTION_ID string = subscription().subscriptionId

// AI Project - Single connection string contains all needed info
output AZURE_AI_PROJECT_CONNECTION_STRING string = '${aiFoundry.outputs.projectEndpoint};subscription_id=${subscription().subscriptionId};resource_group=${rg.name}'
output AZURE_OPENAI_ENDPOINT string = aiFoundry.outputs.endpoint

// AI Search - For RAG knowledge base
output AZURE_SEARCH_ENDPOINT string = enableSearch ? search!.outputs.endpoint : ''
output AZURE_SEARCH_SERVICE_NAME string = enableSearch ? search!.outputs.name : ''

// Container Registry - For Docker image deployment
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.outputs.loginServer
output AZURE_CONTAINER_REGISTRY_NAME string = containerRegistry.outputs.name

// Container Apps - For agent hosting
output AZURE_CONTAINER_APPS_ENVIRONMENT_ID string = containerAppsEnv.outputs.id
output AGENT_MAIN_URL string = deployContainerApps ? 'https://${agentMain!.outputs.fqdn}' : ''
output AGENT_RESEARCHER_URL string = deployContainerApps ? 'https://${agentResearcher!.outputs.fqdn}' : ''
output AGENT_WRITER_URL string = deployContainerApps ? 'https://${agentWriter!.outputs.fqdn}' : ''
output MCP_SERVER_URL string = deployContainerApps ? 'https://${mcpServer!.outputs.fqdn}' : ''
output EVALUATOR_URL string = deployContainerApps ? 'https://${evaluator!.outputs.fqdn}' : ''
