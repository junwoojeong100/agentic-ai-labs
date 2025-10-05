metadata description = 'Creates an Azure Container App in an existing environment.'

@description('Name of the Container App')
param name string

@description('Location for resources')
param location string = resourceGroup().location

@description('Tags for the resource')
param tags object = {}

@description('ID of the Container Apps Environment')
param environmentId string

@description('Container Registry login server')
param containerRegistryName string

@description('Container image name')
param imageName string

@description('CPU cores allocated to the container')
param cpu string = '0.5'

@description('Memory allocated to the container')
param memory string = '1Gi'

@description('Minimum number of replicas')
param minReplicas int = 1

@description('Maximum number of replicas')
param maxReplicas int = 3

@description('Environment variables for the container')
param environmentVariables array = []

@description('Service name for azd tagging')
param serviceName string

@description('Target port for the container')
param targetPort int = 8000

@description('Enable external ingress')
param external bool = true

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: name
  location: location
  tags: union(tags, {
    'azd-service-name': serviceName
  })
  properties: {
    environmentId: environmentId
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: external
        targetPort: targetPort
        transport: 'auto'
        allowInsecure: false
      }
      registries: [
        {
          server: containerRegistryName
          identity: 'system'
        }
      ]
    }
    template: {
      containers: [
        {
          name: serviceName
          image: imageName
          resources: {
            cpu: json(cpu)
            memory: memory
          }
          env: environmentVariables
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// Grant Container App access to Container Registry
resource containerRegistryResource 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' existing = {
  name: containerRegistryName
}

resource acrPullRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerApp.id, containerRegistryResource.id, 'AcrPull')
  scope: containerRegistryResource
  properties: {
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull
  }
}

output id string = containerApp.id
output name string = containerApp.name
output fqdn string = containerApp.properties.configuration.ingress.fqdn
output identityPrincipalId string = containerApp.identity.principalId
