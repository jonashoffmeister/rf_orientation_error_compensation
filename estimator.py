"""
Die Simulation einer sendenden Antenne und einer mobillen empfangenden Antenne,
welche sich zueinander verdrehen (und verschieben, welches aber durch
Verdehungen abgebildet werden kann).
"""
import numpy as np
import matplotlib.pyplot as plt

"""
Funktionsdeklarationen:
"""


def get_distance_2D(x_a, x_b):
    x_ab = x_a - x_b
    dist = ((x_ab[0][0])**2 + (x_ab[1][0])**2)**0.5
    return dist


def get_distance_1D(x_a, x_b):
    dist = abs(x_a - x_b)
    return dist


def h_rss(x_pos_mobil, x_pos_stat, alpha, gamma):
    r = get_distance_2D(x_pos_mobil, x_pos_stat)
    rss = -20*np.log10(r)-r*alpha+gamma
    return rss, r


def h_rss_only(x_pos_mobil, x_pos_stat, alpha, gamma):
    r = get_distance_2D(x_pos_mobil, x_pos_stat)
    rss = -20*np.log10(r)-r*alpha+gamma
    return rss


def h_rss_jacobi(x_pos_mobil, x_pos_stat, alpha):
    r = get_distance_2D(x_pos_mobil, x_pos_stat)
    h_rss_jacobimatrix = np.empty([2, 1])
    h_rss_jacobimatrix[0] = -20*(x_pos_mobil[0]-x_pos_stat[0])/(np.log(10)*r**2)-alpha*(x_pos_mobil[0]-x_pos_stat[0])/r
    h_rss_jacobimatrix[1] = -20*(x_pos_mobil[1]-x_pos_stat[1])/(np.log(10)*r**2)-alpha*(x_pos_mobil[1]-x_pos_stat[1])/r
    return h_rss_jacobimatrix


def measurement_covariance_model(rss_noise_model, r_dist):
    ekf_param = [6.5411, 7.5723, 9.5922, 11.8720, 21.6396, 53.6692, 52.0241]
    r_sig = 50.0  # default (Fuer RSS zwischen -35 und -55 z.Z.)
    if -35 < rss_noise_model or r_dist >= 1900:
        r_sig = 100
    else:
        if rss_noise_model >= -55:
            r_sig = ekf_param[0]
        elif rss_noise_model < -80:
            r_sig = ekf_param[4]
        elif rss_noise_model < -75:
            r_sig = ekf_param[3]
        elif rss_noise_model < -65:
            r_sig = ekf_param[2]
        elif rss_noise_model < -55:
            r_sig = ekf_param[1]
    r_mat = r_sig ** 2
    return r_mat


def ekf_prediction(x_est, p_mat, q_mat):
    x_est = x_est  # + np.random.randn(2, 1) * 1  # = I * x_est
    p_mat = i_mat.dot(p_mat.dot(i_mat)) + q_mat  # Theoretisch mit .T transponierten zweiten I Matrix
    return x_est, p_mat


def ekf_update(rss, tx_pos, tx_alpha, tx_gamma, x_est, p_mat):
    z_meas = rss
    for itx in range(tx_num):
        y_est, r_dist = h_rss(x_est, tx_pos[itx], tx_alpha[itx], tx_gamma[itx])
        y_tild = z_meas[itx] - y_est
        r_mat = measurement_covariance_model(z_meas[itx], r_dist)
        h_jac_mat = h_rss_jacobi(x_est, tx_pos[itx], tx_alpha[itx])
        s_mat = np.dot(h_jac_mat.T, np.dot(p_mat, h_jac_mat)) + r_mat
        k_mat = np.dot(p_mat, (h_jac_mat / s_mat))
        x_est = x_est + np.dot(k_mat, y_tild)
        p_mat = (i_mat - np.dot(k_mat, h_jac_mat.T)) * p_mat
    return x_est, p_mat


"""
Ausfuehrendes Programm:
"""

'''Konfiguration der Messpunkte'''
dist_messpunkte = 25.0
start_messpunkte = np.array([[0.0], [0.0]])

x_n = [start_messpunkte]
while x_n[-1][0] < 1000.0:
    start_messpunkte = start_messpunkte + np.array([[dist_messpunkte], [0.0]])
    x_n.append(start_messpunkte)
while x_n[-1][1] < 1000.0:
    start_messpunkte = start_messpunkte + np.array([[0.0], [dist_messpunkte]])
    x_n.append(start_messpunkte)
while x_n[-1][0] > 0.0:
    start_messpunkte = start_messpunkte + np.array([[-dist_messpunkte], [0.0]])
    x_n.append(start_messpunkte)
while x_n[-1][1] > 0.0:
    start_messpunkte = start_messpunkte + np.array([[0.0], [-dist_messpunkte]])
    x_n.append(start_messpunkte)
anz_messpunkte = len(x_n)

'''Konfiguration der Winkel'''


'''Bestimmung der Messfrequenzen'''
tx_freq = [4.3400e+08, 4.341e+08, 4.3430e+08, 4.3445e+08, 4.3465e+08, 4.3390e+08]
tx_num = len(tx_freq)

'''Postion(en) der stationaeren Antenne(n)'''
tx_pos = [np.array([[-100.9], [-100.9]]), np.array([[500.9], [-100.9]]), np.array([[1100.9], [-100.9]]),
          np.array([[-100.9], [1100.9]]), np.array([[500.9], [1100.9]]), np.array([[1100.9], [1100.9]])]

'''Kennwerte der stationaeren Antenne(n)'''
tx_alpha = np.array([0.01110, 0.01401, 0.01187, 0.01322, 0.01021, 0.01028])
tx_gamma = np.array([-0.49471, -1.24823, -0.17291, -0.61587, 0.99831, 0.85711])

'''Kennwerte der Rauschenden Abweichungen der Antennen'''
tx_sigma = np.array([0.2, 0.2, 0.2, 0.2, 0.2, 0.2])

'''Initialisierung der P-Matrix (Varianz der Position)'''
p_mat = np.array([[100**2, 0], [0, 100**2]])  # Abweichungen von x1 und x2 aufgrund der Messungen...

'''Initialisierung der Q-Matrix (Varianz des Prozessrauschens / Modellunsicherheit)'''
q_mat = np.array([[500**2, 0], [0, 500**2]])  # Abweichungen von x1 und x2 aufgrund des Modelles

'''Initialisierung der y-Matrix fuer die erwartete Messung'''
y_est = np.zeros(tx_num)

'''Initialisierung der F-Matrix -> Gradient von f(x)'''
i_mat = np.eye(2)

'''Initialisierung der Distanzspeicherungsmatrix'''
r_dist = np.zeros(tx_num)

'''Initialisierung der Messmatrix'''
z_meas = np.zeros(tx_num)

'''Initialisierung der geschaetzten Position'''
x_est = np.array([[500.0], [500.0]])

'''Initialisierung der Liste(n) fuer Plots'''
x_est_list = [x_est]

for k in range(anz_messpunkte):
    print "\n \n \nDurchlauf Nummer", k

    rss = np.empty(tx_num)
    for i in range(tx_num):
        rss[i] = h_rss_only(x_n[k], tx_pos[i], tx_alpha[i], tx_gamma[i]) + np.random.randn(1)*tx_sigma[i]
    if k == 15:
        print("RSS:", rss)
    x_est, p_mat = ekf_prediction(x_est, p_mat, q_mat)
    x_est, p_mat = ekf_update(rss, tx_pos, tx_alpha, tx_gamma, x_est, p_mat)

    print "Die wirkliche Position ist: \n", x_n[k]
    print "Die geschaetzte Position ist: \n", x_est
    print "( Die p-Matrix entspricht: \n", p_mat, ")"

    x_est_list.append(x_est)

print('\nFertich!\n')

'''Erstellung der X und Y Koordinatenlisten zum einfachen und effizienteren Plotten'''
x_n_x = [None]*len(x_n)
x_n_y = [None]*len(x_n)
x_est_x = [None]*len(x_est_list)
x_est_y = [None]*len(x_est_list)
tx_pos_x = [None]*len(tx_pos)
tx_pos_y = [None]*len(tx_pos)

for i in range(0, len(x_n)):
    x_n_x[i] = x_n[i][0]
    x_n_y[i] = x_n[i][1]
for i in range(0, len(x_est_list)):
    x_est_x[i] = x_est_list[i][0]
    x_est_y[i] = x_est_list[i][1]
for i in range(0, len(tx_pos)):
    tx_pos_x[i] = tx_pos[i][0]
    tx_pos_y[i] = tx_pos[i][1]

'''Strecke im Scatterplot'''
plt.figure(figsize=(25, 12))
plt.subplot(121)
plt.scatter(x_n_x, x_n_y, marker="^", c='c', s=100)
plt.scatter(x_est_x, x_est_y, marker="o", c='r', s=100)
plt.scatter(tx_pos_x, tx_pos_y, marker="*", c='k', s=100)
xmin = min([min(x_n_x), min(x_est_x), min(tx_pos_x)]) - 100
xmax = max([max(x_n_x), max(x_est_x), max(tx_pos_x)]) + 100
ymin = min([min(x_n_y), min(x_est_y), min(tx_pos_y)]) - 200
ymax = max([max(x_n_y), max(x_est_y), max(tx_pos_y)]) + 100
plt.axis([xmin, xmax, ymin, ymax])
plt.xlabel('X - Achse', fontsize=20)
plt.ylabel('Y - Achse', fontsize=20)
plt.grid()
plt.legend(['Wahre Position', 'Geschaetzte Position', 'Transmitter Antennen'], loc=3)  # best:0, or=1, ol=2, ul=3, ur=4
plt.title('Plot der wahren und geschaetzten Punkte', fontsize=25)
# plt.show()

'''Strecke im Linienplot'''
x_est_fehler = [None]*len((x_est_x))
for i in range(len(x_est_x)):
    x_est_fehler[i] = get_distance_1D(x_est_x[i], x_est_y[i])
# plt.figure(figsize=(12, 12))
plt.subplot(222)
plt.plot(range(1, (len(x_n)+1)), x_n_x)
plt.plot(x_est_x)
plt.plot(range(1, (len(x_n)+1)), x_n_y)
plt.plot(x_est_y)
plt.xlabel('Messungsnummer', fontsize=20)
plt.ylabel('Koordinate', fontsize=20)
plt.legend(['Wahre Position X-Koordinate', 'Geschaetzte X-Koordinate',
            'Wahre Position Y-Koordinate', 'Geschaetzte Y-Korrdinate'], loc=0)
plt.subplot(224)
x_est_fehler = [None]*len((x_est_x))
for i in range(1, len(x_n_x)):
    x_est_fehler[i] = get_distance_1D(x_est_x[i], x_n_x[i-1])
plt.plot(x_est_fehler)
for i in range(1, len(x_n_y)):
    x_est_fehler[i] = get_distance_1D(x_est_y[i], x_n_y[i-1])
plt.plot(x_est_fehler)
for i in range(1, len(x_est_list)):
    x_est_fehler[i] = get_distance_2D(x_est_list[i], x_n[i-1])
plt.plot(x_est_fehler)
plt.xlabel('Messungsnummer', fontsize=20)
plt.ylabel('Fehler', fontsize=20)
plt.legend(['Fehler X-Koordinate', 'Fehler Y-Koordinate', '(Gesamt-) Abstandsfehler'], loc=0)
plt.show()
