import os
from opencmiss.iron import iron

# Problem parameters:
density = 9.0e-4  # in g mm^-3
gravity = [0.0, 0.0, -9.81]  # in m s^-2

numberGlobalElements = [2, 2, 2]
dimensions = [60.0, 40.0, 40.0]
numberOfXi = 3

numberOfLoadIncrements = 3

constitutiveRelation = iron.EquationsSetSubtypes.MOONEY_RIVLIN
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

context = iron.Context()
context.Create(contextUserNumber)

worldRegion = iron.Region()
context.WorldRegionGet(worldRegion)

# Get the number of computational nodes and this computational node number
computationEnvironment = iron.ComputationEnvironment()
context.ComputationEnvironmentGet(computationEnvironment)

worldWorkGroup = iron.WorkGroup()
computationEnvironment.WorldWorkGroupGet(worldWorkGroup)
numberOfComputationalNodes = worldWorkGroup.NumberOfGroupNodesGet()
computationalNodeNumber = worldWorkGroup.GroupNodeNumberGet()

# Create a 3D rectangular cartesian coordinate system
coordinateSystem = iron.CoordinateSystem()
coordinateSystem.CreateStart(coordinateSystemUserNumber,context)
coordinateSystem.CreateFinish()

# Create a region and assign the coordinate system to the region
region = iron.Region()
region.CreateStart(regionUserNumber, worldRegion)
region.LabelSet("Region")
region.CoordinateSystemSet(coordinateSystem)
region.CreateFinish()

# Define basis
basis = iron.Basis()
basis.CreateStart(basisUserNumber,context)
basis.NumberOfXiSet(numberOfXi)
basis.InterpolationXiSet([
        iron.BasisInterpolationSpecifications.LINEAR_LAGRANGE] * numberOfXi)
basis.QuadratureNumberOfGaussXiSet([2] * numberOfXi)
basis.CreateFinish()

# Start the creation of a generated mesh in the region
generatedMesh = iron.GeneratedMesh()
generatedMesh.CreateStart(generatedMeshUserNumber, region)
generatedMesh.TypeSet(iron.GeneratedMeshTypes.REGULAR)
generatedMesh.BasisSet([basis])
generatedMesh.ExtentSet(dimensions)
generatedMesh.NumberOfElementsSet(numberGlobalElements)
mesh = iron.Mesh()
generatedMesh.CreateFinish(meshUserNumber, mesh)

# Create a decomposition for the mesh
decomposition = iron.Decomposition()
decomposition.CreateStart(decompositionUserNumber, mesh)
decomposition.CreateFinish()

# Decompose 
decomposer = iron.Decomposer()
decomposer.CreateStart(decomposerUserNumber,worldRegion,worldWorkGroup)
decompositionIndex = decomposer.DecompositionAdd(decomposition)
decomposer.CreateFinish()

# Create a field for the geometry
geometricField = iron.Field()
geometricField.CreateStart(geometricFieldUserNumber, region)
geometricField.DecompositionSet(decomposition)
geometricField.TypeSet(iron.FieldTypes.GEOMETRIC)
geometricField.VariableLabelSet(iron.FieldVariableTypes.U, "Geometry")
geometricField.CreateFinish()

# Update the geometric field parameters from generated mesh
generatedMesh.GeometricParametersCalculate(geometricField)

# Create the equations_set
equationsSetField = iron.Field()
equationsSet = iron.EquationsSet()
equationsSetSpecification = [iron.EquationsSetClasses.ELASTICITY,
    iron.EquationsSetTypes.FINITE_ELASTICITY,
    constitutiveRelation]
equationsSet.CreateStart(equationsSetUserNumber, region, geometricField,
                         equationsSetSpecification, equationsSetFieldUserNumber, equationsSetField)
equationsSet.CreateFinish()

# Create default materials field
materialField = iron.Field()
equationsSet.MaterialsCreateStart(materialFieldUserNumber, materialField)
equationsSet.MaterialsCreateFinish()

# Create default dependent field
dependentField = iron.Field()
equationsSet.DependentCreateStart(dependentFieldUserNumber, dependentField)
dependentField.VariableLabelSet(iron.FieldVariableTypes.U, "Dependent")
equationsSet.DependentCreateFinish()

# Initialise dependent field from undeformed geometry and displacement bcs and set hydrostatic pressure
for component in range(1, 4):
    iron.Field.ParametersToFieldParametersComponentCopy(
        geometricField, iron.FieldVariableTypes.U, iron.FieldParameterSetTypes.VALUES, component,
        dependentField, iron.FieldVariableTypes.U, iron.FieldParameterSetTypes.VALUES, component)
iron.Field.ComponentValuesInitialiseDP(
    dependentField, iron.FieldVariableTypes.U, iron.FieldParameterSetTypes.VALUES, 4, initialHydrostaticPressure)

# Set constitutive parameters
for component, parameter in enumerate(constitutiveParameters, 1):
    iron.Field.ComponentValuesInitialiseDP(
        materialField,iron.FieldVariableTypes.U,
        iron.FieldParameterSetTypes.VALUES,
        component, parameter)

materialField.ComponentValuesInitialise(
    iron.FieldVariableTypes.V, iron.FieldParameterSetTypes.VALUES, 1, density)

#Create the source field with the gravity vector
sourceField = iron.Field()
equationsSet.SourceCreateStart(sourceFieldUserNumber, sourceField)
equationsSet.SourceCreateFinish()

#Set the gravity vector component values
for component in range(1, 4):
    sourceField.ComponentValuesInitialiseDP(
        iron.FieldVariableTypes.U, iron.FieldParameterSetTypes.VALUES, component, gravity[component - 1])

# Create equations
equations = iron.Equations()
equationsSet.EquationsCreateStart(equations)
equations.SparsityTypeSet(iron.EquationsSparsityTypes.SPARSE)
equations.OutputTypeSet(iron.EquationsOutputTypes.NONE)
equationsSet.EquationsCreateFinish()

# Define the problem
problem = iron.Problem()
problemSpecification = [iron.ProblemClasses.ELASTICITY,
        iron.ProblemTypes.FINITE_ELASTICITY,
        iron.ProblemSubtypes.STATIC_FINITE_ELASTICITY]
problem.CreateStart(problemUserNumber,context,problemSpecification)
problem.CreateFinish()

# Create the problem control loop
problem.ControlLoopCreateStart()
controlLoop = iron.ControlLoop()
problem.ControlLoopGet([iron.ControlLoopIdentifiers.NODE], controlLoop)
controlLoop.MaximumIterationsSet(numberOfLoadIncrements)
problem.ControlLoopCreateFinish()

# Create problem solver
nonLinearSolver = iron.Solver()
linearSolver = iron.Solver()
problem.SolversCreateStart()
problem.SolverGet([iron.ControlLoopIdentifiers.NODE], 1, nonLinearSolver)
nonLinearSolver.outputType = iron.SolverOutputTypes.PROGRESS
nonLinearSolver.NewtonJacobianCalculationTypeSet(iron.JacobianCalculationTypes.FD)
nonLinearSolver.NewtonAbsoluteToleranceSet(1e-14)
nonLinearSolver.NewtonSolutionToleranceSet(1e-14)
nonLinearSolver.NewtonRelativeToleranceSet(1e-14)
nonLinearSolver.NewtonLinearSolverGet(linearSolver)
linearSolver.linearType = iron.LinearSolverTypes.DIRECT
problem.SolversCreateFinish()

# Create solver equations and add equations set to solver equations
solver = iron.Solver()
solverEquations = iron.SolverEquations()
problem.SolverEquationsCreateStart()
problem.SolverGet([iron.ControlLoopIdentifiers.NODE], 1, solver)
solver.SolverEquationsGet(solverEquations)
solverEquations.SparsityTypeSet(iron.SolverEquationsSparsityTypes.SPARSE)
equationsSetIndex = solverEquations.EquationsSetAdd(equationsSet)
problem.SolverEquationsCreateFinish()

# Prescribe boundary conditions
boundaryConditions = iron.BoundaryConditions()
solverEquations.BoundaryConditionsCreateStart(boundaryConditions)

nodes = iron.Nodes()
region.NodesGet(nodes)
eps = 1.0e-10
constrainedNodes = set()
for node in range(1, nodes.NumberOfNodesGet() + 1):
    position = [geometricField.ParameterSetGetNode(
                iron.FieldVariableTypes.U, iron.FieldParameterSetTypes.VALUES,
                1, 1, node, component)
            for component in range(1, 4)]
    # Fix x=0 face
    if abs(position[0]) < eps:
        version = 1
        derivative = 1
        for component in range(1, 4):
            boundaryConditions.AddNode(
                    dependentField, iron.FieldVariableTypes.U,
                    version, derivative, node, component,
                    iron.BoundaryConditionsTypes.FIXED, 0.0)
    # Find nodes to constrain:
    if abs(position[0] - dimensions[0]) < eps:
        constrainedNodes.add(node)

# Constrain nodes at max x end to have the same x component value
version = 1
derivative = 1
component = 1
boundaryConditions.ConstrainNodeDofsEqual(
        dependentField, iron.FieldVariableTypes.U,
        version, derivative, component,
        list(constrainedNodes),1.0)

solverEquations.BoundaryConditionsCreateFinish()

# Solve the problem
problem.Solve()

# Export results
if not os.path.exists('./results'):
    os.makedirs('./results')
fields = iron.Fields()
fields.CreateRegion(region)
fields.NodesExport("./results/Cantilever", "FORTRAN")
fields.ElementsExport("./results/Cantilever", "FORTRAN")
fields.Finalise()
