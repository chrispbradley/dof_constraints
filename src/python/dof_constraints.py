import os
from opencmiss.opencmiss import OpenCMISS_Python as oc

# Problem parameters:
density = 9.0e-4  # in g mm^-3
gravity = [0.0, 0.0, -9.81]  # in m s^-2

numberGlobalElements = [2, 2, 2]
dimensions = [60.0, 40.0, 40.0]
numberOfXi = 3

numberOfLoadIncrements = 3

constitutiveRelation = oc.EquationsSetSubtypes.MOONEY_RIVLIN
c0, c1 = 2.0, 1.0
constitutiveParameters = [c0, c1]
initialHydrostaticPressure = -c0 - 2.0 * c1

# User numbers for identifying OpenCMISS-Iron objects:
contextUserNumber = 1
coordinateSystemUserNumber = 1
regionUserNumber = 1
basisUserNumber = 1
generatedMeshUserNumber = 1
meshUserNumber = 1
decompositionUserNumber = 1
decomposerUserNumber = 1
equationsSetUserNumber = 1
(geometricFieldUserNumber,
    materialFieldUserNumber,
    dependentFieldUserNumber,
    equationsSetFieldUserNumber,
    sourceFieldUserNumber) = range(1, 6)
problemUserNumber = 1

context = oc.Context()
context.Create(contextUserNumber)

worldRegion = oc.Region()
context.WorldRegionGet(worldRegion)

# Get the number of computational nodes and this computational node number
computationEnvironment = oc.ComputationEnvironment()
context.ComputationEnvironmentGet(computationEnvironment)

worldWorkGroup = oc.WorkGroup()
computationEnvironment.WorldWorkGroupGet(worldWorkGroup)
numberOfComputationalNodes = worldWorkGroup.NumberOfGroupNodesGet()
computationalNodeNumber = worldWorkGroup.GroupNodeNumberGet()

# Create a 3D rectangular cartesian coordinate system
coordinateSystem = oc.CoordinateSystem()
coordinateSystem.CreateStart(coordinateSystemUserNumber,context)
coordinateSystem.CreateFinish()

# Create a region and assign the coordinate system to the region
region = oc.Region()
region.CreateStart(regionUserNumber, worldRegion)
region.LabelSet("Region")
region.CoordinateSystemSet(coordinateSystem)
region.CreateFinish()

# Define basis
basis = oc.Basis()
basis.CreateStart(basisUserNumber,context)
basis.NumberOfXiSet(numberOfXi)
basis.InterpolationXiSet([
        oc.BasisInterpolationSpecifications.LINEAR_LAGRANGE] * numberOfXi)
basis.QuadratureNumberOfGaussXiSet([2] * numberOfXi)
basis.CreateFinish()

# Start the creation of a generated mesh in the region
generatedMesh = oc.GeneratedMesh()
generatedMesh.CreateStart(generatedMeshUserNumber, region)
generatedMesh.TypeSet(oc.GeneratedMeshTypes.REGULAR)
generatedMesh.BasisSet([basis])
generatedMesh.ExtentSet(dimensions)
generatedMesh.NumberOfElementsSet(numberGlobalElements)
mesh = oc.Mesh()
generatedMesh.CreateFinish(meshUserNumber, mesh)

# Create a decomposition for the mesh
decomposition = oc.Decomposition()
decomposition.CreateStart(decompositionUserNumber, mesh)
decomposition.CreateFinish()

# Decompose 
decomposer = oc.Decomposer()
decomposer.CreateStart(decomposerUserNumber,worldRegion,worldWorkGroup)
decompositionIndex = decomposer.DecompositionAdd(decomposition)
decomposer.CreateFinish()

# Create a field for the geometry
geometricField = oc.Field()
geometricField.CreateStart(geometricFieldUserNumber, region)
geometricField.DecompositionSet(decomposition)
geometricField.TypeSet(oc.FieldTypes.GEOMETRIC)
geometricField.VariableLabelSet(oc.FieldVariableTypes.U, "Geometry")
geometricField.CreateFinish()

# Update the geometric field parameters from generated mesh
generatedMesh.GeometricParametersCalculate(geometricField)

# Create the equations_set
equationsSetField = oc.Field()
equationsSet = oc.EquationsSet()
equationsSetSpecification = [oc.EquationsSetClasses.ELASTICITY,
    oc.EquationsSetTypes.FINITE_ELASTICITY,
    constitutiveRelation]
equationsSet.CreateStart(equationsSetUserNumber, region, geometricField,
                         equationsSetSpecification, equationsSetFieldUserNumber, equationsSetField)
equationsSet.CreateFinish()

# Create default materials field
materialField = oc.Field()
equationsSet.MaterialsCreateStart(materialFieldUserNumber, materialField)
equationsSet.MaterialsCreateFinish()

# Create default dependent field
dependentField = oc.Field()
equationsSet.DependentCreateStart(dependentFieldUserNumber, dependentField)
dependentField.VariableLabelSet(oc.FieldVariableTypes.U, "Dependent")
equationsSet.DependentCreateFinish()

# Initialise dependent field from undeformed geometry and displacement bcs and set hydrostatic pressure
for component in range(1, 4):
    oc.Field.ParametersToFieldParametersComponentCopy(
        geometricField, oc.FieldVariableTypes.U, oc.FieldParameterSetTypes.VALUES, component,
        dependentField, oc.FieldVariableTypes.U, oc.FieldParameterSetTypes.VALUES, component)
oc.Field.ComponentValuesInitialiseDP(
    dependentField, oc.FieldVariableTypes.U, oc.FieldParameterSetTypes.VALUES, 4, initialHydrostaticPressure)

# Set constitutive parameters
for component, parameter in enumerate(constitutiveParameters, 1):
    oc.Field.ComponentValuesInitialiseDP(
        materialField,oc.FieldVariableTypes.U,
        oc.FieldParameterSetTypes.VALUES,
        component, parameter)

materialField.ComponentValuesInitialise(
    oc.FieldVariableTypes.V, oc.FieldParameterSetTypes.VALUES, 1, density)

#Create the source field with the gravity vector
sourceField = oc.Field()
equationsSet.SourceCreateStart(sourceFieldUserNumber, sourceField)
equationsSet.SourceCreateFinish()

#Set the gravity vector component values
for component in range(1, 4):
    sourceField.ComponentValuesInitialiseDP(
        oc.FieldVariableTypes.U, oc.FieldParameterSetTypes.VALUES, component, gravity[component - 1])

# Create equations
equations = oc.Equations()
equationsSet.EquationsCreateStart(equations)
equations.SparsityTypeSet(oc.EquationsSparsityTypes.SPARSE)
equations.OutputTypeSet(oc.EquationsOutputTypes.NONE)
equationsSet.EquationsCreateFinish()

# Define the problem
problem = oc.Problem()
problemSpecification = [oc.ProblemClasses.ELASTICITY,
        oc.ProblemTypes.FINITE_ELASTICITY,
        oc.ProblemSubtypes.STATIC_FINITE_ELASTICITY]
problem.CreateStart(problemUserNumber,context,problemSpecification)
problem.CreateFinish()

# Create the problem control loop
problem.ControlLoopCreateStart()
controlLoop = oc.ControlLoop()
problem.ControlLoopGet([oc.ControlLoopIdentifiers.NODE], controlLoop)
controlLoop.MaximumIterationsSet(numberOfLoadIncrements)
problem.ControlLoopCreateFinish()

# Create problem solver
nonLinearSolver = oc.Solver()
linearSolver = oc.Solver()
problem.SolversCreateStart()
problem.SolverGet([oc.ControlLoopIdentifiers.NODE], 1, nonLinearSolver)
nonLinearSolver.outputType = oc.SolverOutputTypes.PROGRESS
nonLinearSolver.NewtonJacobianCalculationTypeSet(oc.JacobianCalculationTypes.EQUATIONS)
nonLinearSolver.NewtonAbsoluteToleranceSet(1e-14)
nonLinearSolver.NewtonSolutionToleranceSet(1e-14)
nonLinearSolver.NewtonRelativeToleranceSet(1e-14)
nonLinearSolver.NewtonLinearSolverGet(linearSolver)
linearSolver.linearType = oc.LinearSolverTypes.DIRECT
problem.SolversCreateFinish()

# Create solver equations and add equations set to solver equations
solver = oc.Solver()
solverEquations = oc.SolverEquations()
problem.SolverEquationsCreateStart()
problem.SolverGet([oc.ControlLoopIdentifiers.NODE], 1, solver)
solver.SolverEquationsGet(solverEquations)
solverEquations.SparsityTypeSet(oc.SolverEquationsSparsityTypes.SPARSE)
equationsSetIndex = solverEquations.EquationsSetAdd(equationsSet)
problem.SolverEquationsCreateFinish()

# Prescribe boundary conditions
boundaryConditions = oc.BoundaryConditions()
solverEquations.BoundaryConditionsCreateStart(boundaryConditions)

nodes = oc.Nodes()
region.NodesGet(nodes)
eps = 1.0e-10
constrainedNodes = set()
for node in range(1, nodes.NumberOfNodesGet() + 1):
    position = [geometricField.ParameterSetGetNode(
                oc.FieldVariableTypes.U, oc.FieldParameterSetTypes.VALUES,
                1, 1, node, component)
            for component in range(1, 4)]
    # Fix x=0 face
    if abs(position[0]) < eps:
        version = 1
        derivative = 1
        for component in range(1, 4):
            boundaryConditions.AddNode(
                    dependentField, oc.FieldVariableTypes.U,
                    version, derivative, node, component,
                    oc.BoundaryConditionsTypes.FIXED, 0.0)
    # Find nodes to constrain:
    if abs(position[0] - dimensions[0]) < eps:
        constrainedNodes.add(node)

# Constrain nodes at max x end to have the same x component value
version = 1
derivative = 1
component = 1
boundaryConditions.ConstrainNodeDofsEqual(
        dependentField, oc.FieldVariableTypes.U,
        version, derivative, component,
        list(constrainedNodes),1.0)

solverEquations.BoundaryConditionsCreateFinish()

# Solve the problem
problem.Solve()

# Export results
if not os.path.exists('./results'):
    os.makedirs('./results')
fields = oc.Fields()
fields.CreateRegion(region)
fields.NodesExport("./results/Cantilever", "FORTRAN")
fields.ElementsExport("./results/Cantilever", "FORTRAN")
fields.Finalise()
