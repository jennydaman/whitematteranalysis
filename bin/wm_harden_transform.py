#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os

from joblib import Parallel, delayed

import whitematteranalysis as wma


def _build_arg_parser():

    parser = argparse.ArgumentParser(
        description="Harden transform with Slicer.",
        epilog="Written by Fan Zhang, fzhang@bwh.harvard.edu")
    parser.add_argument(
        'inputDirectory',
        help='Directory of input VTK/VTP files that are going to be transformed.')
    parser.add_argument(
        'outputDirectory',
        help='Directory of output transformed results.')
    parser.add_argument(
        'Slicer',
        help='Path of 3D Slicer.')
    parser.add_argument(
        '-t', dest="transform_file",
        help='Individual transform matrix file. If this is assigned, all input files will be transformed with this transform matrix.')
    parser.add_argument(
        '-ts', dest="transform_folder",
        help='Folder of multiple transform matrix files. If this is assigned, input files will be transformed with different transform matrices. Make sure that the input and transform files match each other in alphabetical order.')
    parser.add_argument(
        '-i', action = 'store_true', dest = "inverse_transform",
        help='Inverse transform if given.')
    parser.add_argument(
        '-j', action="store", dest="numberOfJobs", type=int,
        help='Number of processors to use.')

    return parser


def _parse_args(parser):

    return parser.parse_args()


def main():

    parser = _build_arg_parser()
    args = _parse_args(parser)

    inputdir = os.path.abspath(args.inputDirectory)
    if not os.path.isdir(args.inputDirectory):
        print(f"Error: Input directory {args.inputDirectory} does not exist.")
        exit()
    
    outdir = os.path.abspath(args.outputDirectory)
    if not os.path.exists(args.outputDirectory):
        print(f"Output directory {args.outputDirectory} does not exist, creating it.")
        os.makedirs(outdir)
    
    slicer_path = os.path.abspath(args.Slicer)
    if not os.path.exists(args.Slicer):
        print(f"Error: 3D Slicer {args.Slicer} does not exist.")
        exit()
    
    if (args.transform_file is None and args.transform_folder is None) or \
        (args.transform_file is not None and args.transform_folder is not None):
        print("Error: Either -t or -ts needs be provided.")
        exit()
    elif args.transform_file is not None:
        transform_way = 'individual'
        transform_path = os.path.abspath(args.transform_file)
        if not os.path.isfile(args.transform_file):
            print(f"Error: Input transform file {args.transform_file} does not exist or it is not a file.")
            exit()
    elif args.transform_folder is not None:
        transform_way = 'multiple'
        transform_path = os.path.abspath(args.transform_folder)
        if not os.path.isdir(args.transform_folder):
            print(f"Error: Input transform file folder {args.transform_folder} does not exist.")
            exit()
    
    inverse = args.inverse_transform
    
    if args.numberOfJobs is not None:
        number_of_jobs = args.numberOfJobs
    else:
        number_of_jobs = 1
    
    input_polydatas = wma.io.list_vtk_files(inputdir)
    number_of_polydatas = len(input_polydatas)
    
    if transform_way == 'multiple':
        input_transforms = wma.io.list_transform_files(transform_path)
        number_of_transforms = len(input_transforms)
        if number_of_polydatas != number_of_transforms:
            print(f"Error: The number of input VTK/VTP files {number_of_polydatas} should be equal to the number of transform files {number_of_transforms}")
            exit()
    
    print(f"<{os.path.basename(__file__)}> Starting harden transforms.")
    print("")
    print(f"=====input directory======\n {inputdir}")
    print(f"=====output directory=====\n {outdir}")
    print(f"=====3D Slicer====\n {slicer_path}")
    print(f"=====Way of transform====\n {transform_way}")
    print(f"=====Inverse? ====\n {inverse}")
    print(f"=====Transform file(s) path====\n {transform_path}")
    print(f"=====Number of jobs:====\n {number_of_jobs}")
    
    def command_harden_transform(polydata, transform, inverse, slicer_path, outdir):
        if inverse:
            str_inverse = 1
        else:
            str_inverse = 0
    
        print(f"<{os.path.basename(__file__)}> Transforming: {polydata}")
        cmd = f"{slicer_path} --no-main-window --python-script $(which harden_transform_with_slicer.py) {polydata} {transform} {str(str_inverse)} {outdir} --python-code 'slicer.app.quit()' >> f{os.path.join(outdir, 'log.txt 2>&1')}"
    
        os.system(cmd)
    
    if transform_way == 'multiple':
        for polydata, transform in zip(input_polydatas, input_transforms):
            print(f"====== {transform} <TO> {polydata}")
        print("\n")
        Parallel(n_jobs=number_of_jobs, verbose=1)(
            delayed(command_harden_transform)(polydata, transform, inverse, slicer_path, outdir)
            for polydata, transform in zip(input_polydatas, input_transforms))
    else:
        print(f"====== {transform_path} will be applied to all inputs.\n")
    
        command_harden_transform(inputdir, transform_path, inverse, slicer_path, outdir)
    
        # Parallel(n_jobs=number_of_jobs, verbose=1)(
        #     delayed(command_harden_transform)(polydata, transform_path, inverse, slicer_path, outdir)
        #     for polydata in input_polydatas)
    
    output_polydatas = wma.io.list_vtk_files(outdir)
    number_of_results = len(output_polydatas)
    print(f"<{os.path.basename(__file__)}> Transform were conducted for {number_of_results} subjects.")
    
    if number_of_results != number_of_polydatas:
        print("Error: The numbers of inputs and outputs are different. Check log file for errors.")
    else:
        os.remove(os.path.join(outdir, 'log.txt'))

if __name__ == '__main__':
    main()
