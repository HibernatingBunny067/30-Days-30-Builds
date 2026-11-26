"""
Kalman filter for a linear system
"""
import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

class KalmanFilter:
    def __init__(self, P_init,R_init, Q_init, H_mat, dt, sys, x0):

        self.P_init = P_init
        self.R_init = R_init
        self.Q_init = Q_init
        self.dt = dt
        self.H_mat = H_mat
        self.sys = sys
        self.x0 = x0
        self.t0 = 0.0

    def predict(self):
        """
        Evolve the system in time and predict
        """

        solution = solve_ivp(self.sys,[self.t0,self.t0+self.dt],self.x0)

        self.t0 = self.t0 + self.dt
        self.x0 = self.x0 + solution.y[-1]

    def gain(self):
        pass


    def update(self,measurement):
        """
        update the prediction based on measurement
        """
        y = measurement - self.H_mat@self.x0
        S = self.H_mat@self.P_init@self.H_mat.T + self.R_init

        K = self.P_init@self.H_mat.T@np.linalg.inv(S)

        self.x0 = self.x0 + K@y
        self.P_init = (np.eye(np.ones_like(K@self.H_mat).shape[0])-K@self.H_mat)@self.P_init







def main():
    pass

if __name__ == "__main__":
    main()
