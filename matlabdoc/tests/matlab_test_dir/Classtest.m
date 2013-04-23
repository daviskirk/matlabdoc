classdef TestClass < InheritClass1 & InheritClass2
    properties
        property1
        property2withDefault = 12313;
        property3
    end
    methods
        function obj = SuperelementBuilder(varargin)
        %Constructor docstring
        %
        % third line
            obj.property1 = 123
        end

        function something = method1(obj, arg1)
            something = None
        end
    end
end
