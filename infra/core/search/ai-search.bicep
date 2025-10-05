// Azure AI Search service for RAG knowledge base

metadata description = 'Creates an Azure AI Search service.'

@description('The name of the search service')
param name string

@description('Location for the search service')
param location string = resourceGroup().location

@description('Tags for the search service')
param tags object = {}

@description('The pricing tier of the search service')
param sku object = {
  name: 'basic'
}

@description('Replicas distribute search workloads across the service')
@minValue(1)
@maxValue(12)
param replicaCount int = 1

@description('Partitions allow for scaling of document count as well as faster indexing')
@minValue(1)
@maxValue(12)
param partitionCount int = 1

@allowed([
  'default'
  'highDensity'
])
@description('Applicable only for SKU set to standard3. You can set this property to enable a single, high density partition that allows up to 1000 indexes.')
param hostingMode string = 'default'

@allowed([
  'enabled'
  'disabled'
])
@description('Network access control for the search service')
param publicNetworkAccess string = 'enabled'

resource search 'Microsoft.Search/searchServices@2024-06-01-preview' = {
  name: name
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  sku: sku
  properties: {
    replicaCount: replicaCount
    partitionCount: partitionCount
    hostingMode: hostingMode
    publicNetworkAccess: publicNetworkAccess
    disableLocalAuth: false
    semanticSearch: 'free'
  }
}

output id string = search.id
output name string = search.name
output endpoint string = 'https://${search.name}.search.windows.net/'
output principalId string = search.identity.principalId
