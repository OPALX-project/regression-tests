import math
import os
import numpy
import matplotlib
import matplotlib.pyplot

import pyopal.objects.parser
import pyopal.objects.field
import pyopal.objects.ffa_field_mapper

"""
Small helper script for debugging the VFFA. Plots the field map and prints out
the element locations
"""

def load_opal_lattice(lattice_file_name):
    path = os.path.abspath(__file__) # assume path is in the same directory as this script
    path = os.path.split(path)[0]
    os.chdir(path)
    pyopal.objects.parser.initialise_from_opal_file(lattice_file_name)
    print(f"Initialised {lattice_file_name}")

def make_plot(r_list):
    mapper = pyopal.objects.ffa_field_mapper.FFAFieldMapper()
    mapper.load_tracks("VFFA-1-trackOrbit.dat")
    mapper.x_points = numpy.linspace(-20.0, 20.0, 400)
    mapper.y_points = numpy.linspace(-20.0, 20.0, 400)
    figure = mapper.field_map_cartesian()
    mapper.plot_tracks_cartesian(figure.axes[0])
    for r in r_list:
        x = [r*math.sin(2*math.pi*i/100) for i in range(101)]
        y = [r*math.cos(2*math.pi*i/100) for i in range(101)]
        figure.axes[0].plot(x, y, linestyle="-", color="grey")
    figure.save("field_map.png")

def list_elements():
    old_start_dir = 90.0
    print(f"  i {'NAME'.ljust(20)} {'R0'.rjust(8)} {'PHI0'.rjust(8)} {'DIR'.rjust(8)}")
    for i in range(pyopal.objects.field.get_number_of_elements()):
        name = pyopal.objects.field.get_element_name(i)
        start = pyopal.objects.field.get_element_start_position(i)
        normal = pyopal.objects.field.get_element_start_normal(i)
        start_r = (start[0]**2+start[1]**2)**0.5
        start_phi = math.degrees(math.atan2(start[1], start[0]))
        new_start_dir = math.degrees(math.atan2(normal[1], normal[0]))
        print(f"{i:3d} {name.ljust(20)} {start_r:8.5g} {start_phi:8.5g} {new_start_dir-old_start_dir:8.5g}")
        old_start_dir = new_start_dir

def main():
    load_opal_lattice("VFFA-1.in")
    make_plot([14.0])
    list_elements()

if __name__ == "__main__":
    main()
    matplotlib.pyplot.show(block=False)
    input("Press <CR> to finish")