class User:
    _id_counter = 0  
    
    def __init__(self, ip=None, x=0,y=0,z=0,satellites=None):
        User._id_counter += 1
        self.id = User._id_counter
        self.ip = ip
        self.satellite_lst = satellites #список использунмых спутников
        self._x = x
        self._y = y
        self._z = z

        self._dx = 0
        self._dy = 0
        self._dz = 0


    @property
    def x (self):# геттер
        return self._x
    @x.setter # сеттер
    def x (self, x):
        self._x = x

    @property
    def z (self):# геттер
        return self._z
    @z.setter # сеттер
    def z (self, z):
        self._z = z

    @property
    def y (self):# геттер
        return self._y
    @y.setter # сеттер
    def y (self, y):
        self._y = y


    @property
    def dx(self): return self._dx
    @dx.setter
    def dx(self, v): self._dx = v

    @property
    def dy(self): return self._dy
    @dy.setter
    def dy(self, v): self._dy = v

    @property
    def dz(self): return self._dz
    @dz.setter
    def dz(self, v): self._dz = v