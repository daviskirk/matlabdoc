classdef SuperelementBuilder
%% Create a Superelement object with specific dimensions and properties
%
% Class:
%     classdef MyClass;
%
% Author:
%     Davis Kirkendall
%
% Description:
%
%     Class to describe a Superelement in the form of mbs3d bodies and
%     joints. In theory, each superelement consists of 4 bodies.  In this
%     implementation however, each superelement consists of 6 bodies
%     (called elements from here on) and 6 joints whereas 2 of the bodies
%     are massless and lengthless (elem2 and 5) in order to generate
%     universal joints. The weld joint at the start of the superelement is
%     for convinience and connecting multiple superelements together.
%
%                   elem1     elem2  elem3      elem4  elem5   elem6
%                /+-----------+ +||+-------+  +-------+||+ +-----------+
%                /|           |  |||       |  |       |||  |           |
%     weld joint /|           |O |||       |==|       ||| O|           |
%                /|           |  |||       |  |       |||  |           |
%                /+-----------+ +||+-------+  +-------+||+ +-----------+
%                              ^  ^         ^          ^  ^
%                              |  |         |          |  |
%                             /   |      x-revolute    |   \
%                    y-revolute  z-revolute      y-revolute  z-revolute
%
%
%
% MyClass properties:
%
%     Tbody − struct holding body attributes of elements
%
%     Tjoint − struct holding joint attributes
%
%
% Myclass methods:
%
%     Superelement − Constructor Method
%
%     createSuperelement - create new superelement
%
%     TODO: describe methods
%
% Examples:
%     TODO: write examples
%
% See Also: TODO: RELATEDFUNCTION, RELATEDCLASS

properties(Constant, Hidden)
    NELEMS_PER_SE = 6;
    NJOINTS_PER_SE = 6;
    OUTER_ELEM_LENGTH_RATIO = 0.5*(1-1/sqrt(3));
    INNER_ELEM_LENGTH_RATIO = 0.5*(1/sqrt(3));
    ELEM_LENGTH_RATIO = ...
	[ SuperelementBuilder.OUTER_ELEM_LENGTH_RATIO
	  0
	  SuperelementBuilder.INNER_ELEM_LENGTH_RATIO
	  SuperelementBuilder.INNER_ELEM_LENGTH_RATIO
	  0
	  SuperelementBuilder.OUTER_ELEM_LENGTH_RATIO ];
    LOCAL_UNIT_VECTORS = ...
	{ [1,0,0; 0,1,0]'
	  [0,1,0; 0,0,1]'
	  [0,0,1; 1,0,0]'
	  [1,0,0; 0,0,1]'
	  [0,0,1; 0,1,0]'
	  [0,1,0; 1,0,0]'};
    ELEM_BODY_NAME = {'Elem1', 'UJ1', 'Elem2', 'Elem3', 'UJ2', 'Elem4'};
    ELEM_JOINT_NAME = {'Weld', 'U1Y', 'U1Z', 'RX', 'U2Z', 'U2Y'};
    INDEPENDENT_JOINT_INDEX = 1:6
    BODY_PARENT = 0:5
end

properties (SetAccess = protected)
    Tbody;
    Tjoint;
end % properties

properties (Dependent)
    nSe
end

methods
    function obj = SuperelementBuilder(varargin)
    %SUPERELEMENT creates a Superelement
    %
    % function obj = Superelement(geometryDescr, Geometry, rho, E, G, rayleigh)
    % where geometryDescr is one if 'brick' or 'cylinder', Geometry is a vector
    % with components [length, width, height] ([length, radius]) for 'brick'
    % ('cylinder').  The Geometry vector can have an optional 4th (3rd)
    % component describing the thickness in which case the body is assumed to
    % be a tube-like body with walls of the given thickness.
	if nargin == 0
	    return
	end
	In = obj.parseInput(varargin{:});
	for iSe = 1:In.nSe
	    SeIn = obj.calcSuperelementParams(iSe, In);
	    if iSe == 1 % start chain
		obj = obj.makeSingleSuperelement(SeIn);
	    else % connect to existing chain
		obj = [obj obj.makeSingleSuperelement(SeIn)];
	    end
	end
    end

    function obj = makeSingleSuperelement(obj, In)
    %MAKESINGLESUPERELEMENT short summary
    %
    % obj = makeSingleSuperelement(varargin)
    %
	mass = calcMass(In.geometryDescr, In.Geometry, In.rho);
	InertiaCm = calcInertiaCm(In.geometryDescr, In.Geometry, mass);

	obj.Tbody=initTbody(obj.NELEMS_PER_SE);
	obj.Tjoint=initTjoints(obj.NJOINTS_PER_SE);

	for iE = 1:obj.NELEMS_PER_SE
	    ElemGeometry = obj.calcElemGeometry(iE, In.Geometry);

	    obj.Tbody(iE).name = obj.ELEM_BODY_NAME{iE};
	    obj.Tbody(iE).localPoints = ...
		obj.calcLocalPoints(In.geometryDescr, ElemGeometry);
	    obj.Tbody(iE).cogPoint = 3;
	    obj.Tbody(iE).localUnitVectors = obj.LOCAL_UNIT_VECTORS{iE};
	    obj.Tbody(iE).Aini = eye(3);

	    obj.Tbody(iE).mass = ...
		calcMass(In.geometryDescr, ElemGeometry, In.rho);
	    obj.Tbody(iE).Jlocal = calcInertiaCm(In.geometryDescr, ...
						 ElemGeometry, ...
						 obj.Tbody(iE).mass);

	    if ~any(iE == [2,5])
		obj.Tbody(iE).linesToDraw = [1 2];
	    end

	    obj.Tjoint(iE).name=obj.ELEM_JOINT_NAME{iE};
	    if iE == 1
		obj.Tjoint(iE).type='P'; % prismatic joint with infinite
					 % damping as weld joint??
	    else
		obj.Tjoint(iE).type='R';
	    end

	    [obj.Tjoint(iE).k, obj.Tjoint(iE).cv] = obj.calcElemSpringAndDampCoeff(...
		iE, In.Geometry, InertiaCm, In.E, In.G, In.rayleighDampingCoeff);

	    obj.Tjoint(iE).bodies=[iE-1, iE];
	    obj.Tjoint(iE).points=[2 1];
	    obj.Tjoint(iE).vectors=[2 1];
	    obj.Tjoint(iE).zPosIni=0;
	    obj.Tjoint(iE).zVelIni=0;
	end
    end % make single

    function obj = horzcat(obj, varargin)
    %HORZCAT chain multiple superelements together
    %
    % obj = horzcat(obj, varargin)
    %
	for iObj = 1:length(varargin)
	    % Add bodies
	    nNew = length(varargin{iObj}.Tbody);
	    obj.Tbody(end+1:end+nNew) = varargin{iObj}.Tbody;
	    % Add joints
	    nNew = length(varargin{iObj}.Tjoint);
	    obj.Tjoint(end+1:end+nNew) = varargin{iObj}.Tjoint;
	end
    end

    function nSe = get.nSe(obj)
	nSe = length(obj.Tbody)/obj.NELEMS_PER_SE;
    end

end %public methods

methods(Hidden)
    function varargout = testMethod(obj, methodName, varargin)
	[varargout{1:nargout}] = feval(methodName, obj, varargin{:});
    end
end

methods(Access = protected)
    function Param = parseInput(obj, varargin)
	chkGeometryDescr = @(x) any(validatestring(x, {'brick','cylinder'}));
	chkScalarLeq0 = ...
	    @(x) validateattributes(x, {'numeric'}, {'scalar', '>=', 0});
	chkScalarL0 = ...
	    @(x) validateattributes(x, {'numeric'}, {'scalar', '>', 0});
	chkVecLeq0 = ...
	    @(x) validateattributes(x, {'numeric'}, {'vector', '>=', 0});

	p = inputParser;
	p.addRequired('nSe', chkScalarL0);
	p.addRequired('geometryDescr', chkGeometryDescr);
	p.addRequired('Geometry', chkVecLeq0);
	p.addRequired('rho', chkScalarLeq0);
	p.addRequired('E', chkScalarL0);
	p.addRequired('G', chkScalarL0);
	p.addRequired('rayleighDampingCoeff', chkScalarL0);

	p.parse(varargin{:});
	Param = p.Results;
    end

    function ParamStruct = calcSuperelementParams(obj, iSe, InStruct)
    %CALCSUPERELEMENTPARAMS get new Parameters for a sub-Superelement
    %
    % ParamStruct = calcSuperelementParams(obj, iSe, InStruct)
    %
	ParamStruct = InStruct;
	switch InStruct.geometryDescr
	  case 'brick'
	    ParamStruct.Geometry(1) = InStruct.Geometry(1)/InStruct.nSe;
	  case 'cylinder'
	    % TODO: implement tapering Superelements, cones
	    % length
	    ParamStruct.Geometry(1) = InStruct.Geometry(1)/InStruct.nSe;
	  case 'cone'
	    ParamStruct.geometryDescr = 'cylinder';
	    % split radius into superlements in cylinder form
	    ParamStruct.Geometry(1) = InStruct.Geometry(1)/InStruct.nSe;
	    ParamStruct.Geometry(2) = ...
		InStruct.Geometry(2) ...
		- (InStruct.Geometry(2) - InStruct.Geometry(3)) ...
		/ InStruct.nSe*(iSe - 0.5);
	    % cylinders only need one radius
	    ParamStruct.Geometry(3) = [];
	    % TODO: implement tapering wall thickness
	end
    end

    function ElemGeometry = calcElemGeometry(obj, iE, SeGeometry)
	ElemGeometry = SeGeometry;
	ElemGeometry(1) = SeGeometry(1)*SuperelementBuilder.ELEM_LENGTH_RATIO(iE);
    end

    function CenterOfMass = calcCenterOfMass(obj, geometryDescr, Geometry)
    %CALCCENTEROFMASS calculate point of center of mass
    %
    % calcCenterOfMass(obj, geometryDescr, Geometry) calculates the center
    % of mass relative to the base point of the body with the geometry given
    % by the string in geometryDescr and the vector in Geometry.
	CenterOfMass = zeros(3,1);
	switch geometryDescr
	  case {'brick', 'cylinder'}
	    CenterOfMass(1) = Geometry(1)/2;
	  otherwise
	    error('No GeometryDescr %s', ...
		  geometryDescr);
	end
    end

    function LocalPoints = calcLocalPoints(obj, geometryDescr, Geometry)
    % CALCLOCALPOINTS calculate local points of a body
    %
    % calcLocalPoints(obj, geometryDescr, Geometry) calculate local points of a
    % body with geometryDescr as a string and Geometry as the Geometry array
    % of the body
	LocalPoints = zeros(3,3);
	LocalPoints(1,2) = Geometry(1);
	LocalPoints(:,3) = obj.calcCenterOfMass(geometryDescr, Geometry);
    end

    function [springCoeff, dampCoeff] = calcElemSpringAndDampCoeff(...
	obj, elemJoint, SeGeometry, SeInertiaCm, E, G, rayleighDampingCoeff)
	% CALCELEMSPRINGANDDAMPCOEFF calc elem spring and damping coefficients
	%
	% [springCoeff, dampCoeff] = calcElemSpringAndDampCoeff(obj, iE, SeGeometry, SeInertiaCm)
	% Calculates the spring and damping coefficients for the element
	% with the index iE, according to the Geometry vector of the
	% superelement SeGeometry and the Inertia tensor of the Superelement
	% SeInertia
	if ischar(elemJoint)
	    jointName = elemJoint;
	else
	    jointName = obj.ELEM_JOINT_NAME{elemJoint};
	end

	switch jointName
	  case {'U1Y', 'U2Y'}
	    springCoeff = 2*E*SeInertiaCm(2,2)/SeGeometry(1);
	    dampCoeff = rayleighDampingCoeff * springCoeff;
	  case {'U1Z', 'U2Z'}
	    springCoeff = 2*E*SeInertiaCm(3,3)/SeGeometry(1);
	    dampCoeff = rayleighDampingCoeff * springCoeff;
	  case {'TX', 'RX'}
	    springCoeff = G*SeInertiaCm(1,1)/SeGeometry(1);
	    dampCoeff = rayleighDampingCoeff * springCoeff;
	  case {'Weld', 'W'}
	    springCoeff = 0;
	    dampCoeff = inf; % rigid
	end
    end
end % protected methods
end% classdef
