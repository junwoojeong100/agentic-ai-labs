param name string
param location string = resourceGroup().location
param tags object = {}
param sku object = {
  name: 'S0'
}
param deployments array = []

resource account 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = {
  name: name
  location: location
  tags: tags
  kind: 'AIServices'
  sku: sku
  properties: {
    customSubDomainName: name
    publicNetworkAccess: 'Enabled'
  }
}

@batchSize(1)
resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = [for deployment in deployments: {
  parent: account
  name: deployment.name
  sku: deployment.sku
  properties: {
    model: deployment.model
    raiPolicyName: contains(deployment, 'raiPolicyName') ? deployment.raiPolicyName : null
  }
}]

output id string = account.id
output name string = account.name
output endpoint string = account.properties.endpoint
