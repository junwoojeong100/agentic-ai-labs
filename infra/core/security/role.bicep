// Role assignment module

@description('Principal ID to assign the role to')
param principalId string

@description('Role definition ID (GUID)')
param roleDefinitionId string

@description('Principal type')
@allowed([
  'User'
  'Group'
  'ServicePrincipal'
])
param principalType string = 'ServicePrincipal'

// Role assignment
resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(principalId, roleDefinitionId, resourceGroup().id)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionId)
    principalId: principalId
    principalType: principalType
  }
}

output roleAssignmentId string = roleAssignment.id
