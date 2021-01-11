import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

# Define some points:
points = np.array([[0, 3, 10, 13],
                   [0, 0, -10, -10]]).T  # a (nbre_points x nbre_dim) array

# Linear length along the line:
distance = np.cumsum( np.sqrt(np.sum( np.diff(points, axis=0)**2, axis=1 )) )
distance = np.insert(distance, 0, 0)/distance[-1]
diff_dist = np.sqrt(np.sum( np.diff(points, axis=0)**2, axis=1 ))
print(diff_dist)
dist_sum = np.sum(diff_dist)
diff_dist = diff_dist / dist_sum
print(diff_dist)

# Interpolation for different methods:
interpolations_methods = ['quadratic']
num_points = 23
alpha = np.linspace(0, 1, num_points)

points_too_much = diff_dist * num_points
print(points_too_much)
points_too_much = np.round(points_too_much,0)

interpolated_points = {}
for method in interpolations_methods:
    interpolator =  interp1d(distance, points, kind=method, axis=0)
    interpolated_points[method] = interpolator(alpha)

# Graph:
plt.figure(figsize=(7,7))
for method_name, curve in interpolated_points.items():
    plt.plot(*curve.T, '.', label=method_name);

new_curve = curve[int(points_too_much[0]):-int(points_too_much[-1])]
print(new_curve.shape)
lenght = len(new_curve)-2
a = np.zeros((lenght, lenght))
b = np.zeros((lenght, lenght))
np.fill_diagonal(a, 1)
np.fill_diagonal(b, -1)
d = np.zeros((lenght,2))
a = np.c_[d, a]
b = np.c_[b, d]
a = a + b
c = np.dot(a, new_curve)
e = np.zeros((c.shape))
e[:, 0] = c[:, 1]
e[:, 1] = -c[:, 0]
f = np.sum(np.abs(e)**2,axis=-1)**(1./2)
f = np.array([f])
e = e / f.T


distance2 = np.cumsum( np.sqrt(np.sum( np.diff(new_curve, axis=0)**2, axis=1 )) )
distance2 = np.insert(distance2, 0, 0)/distance2[-1]
distance2 = np.array([distance2])
print(e)
print(distance2)

width_pred = 4
width_succ = 2
h = (1 - (distance2 * (width_succ / width_pred))).T
h = h[1:-1]
e = e * h * width_pred
#print(h)
print(e)
#e = e + (distance2 * (width_pred - (width_pred-width_succ)) / 2)
g = np.concatenate((np.array([[-1,-2]]),e),axis=0)
g = np.concatenate((g,np.array([[0,-1]])),axis=0)

#print((width_pred - (distance2 * (width_pred - width_succ))) / 2)
#f = g * ((width_pred - (distance2 * (width_pred-width_succ))) / 2).T
f = new_curve + g


plt.plot(*points.T, 'ok', label='original points')
plt.plot(*f.T, 'ok', label='e points')
plt.axis('equal'); plt.legend(); plt.xlabel('x'); plt.ylabel('y')
plt.show()