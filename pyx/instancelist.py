class InstanceList:

    def AllowedInstances(self, Instances, AllowedClassesOnce, AllowedClassesMultiple = []):
        for i in range(len(Instances)):
            for j in range(len(AllowedClassesOnce)):
                if isinstance(Instances[i], AllowedClassesOnce[j]):
                    del AllowedClassesOnce[j]
                    break
            else:
                for j in range(len(AllowedClassesMultiple)):
                    if isinstance(Instances[i], AllowedClassesMultiple[j]):
                        break
                else:
                    assert 0, "instance not allowed"

    def ExtractInstance(self, Instances, Class, DefaultInstance = None):
        for Instance in Instances:
            if isinstance(Instance, Class):
                return Instance
        return DefaultInstance

    def ExtractInstances(self, Instances, Class, DefaultInstances = []):
        Result = []
        for Instance in Instances:
            if isinstance(Instance, Class):
                Result = Result + [ Instance, ]
        if len(Result) == 0:
            return DefaultInstance
        else:
            return Result



