#!/usr/bin/env python3
import os
from matplotlib import font_manager as fm, rcParams
import baltic as bt

import re
import copy

import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib import cm
import matplotlib.patheffects as path_effects
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Polygon
import matplotlib.lines as mlines
import matplotlib.patches as mpatches

import numpy as np
from scipy.special import binom
import math

import itertools
import requests

from io import StringIO as sio
from io import BytesIO as csio
from Bio import Phylo
from collections import defaultdict

import datetime as dt
from collections import Counter
from collections import defaultdict


thisdir = os.path.abspath(os.path.dirname(__file__))

def find_tallest_tree(input_dir):
    tree_heights = []
    
    for r,d,f in os.walk(input_dir):
        for fn in f:
            if fn.endswith(".tree"):
               
                tree_file = os.path.join(r, fn)
                tree = bt.loadNewick(tree_file,absoluteTime=False)
                tips = []
                
                for k in tree.Objects:
                    if k.branchType == 'leaf':
                        tips.append(k.name)
                
                tree_heights.append(tree.treeHeight)
    
    max_height = sorted(tree_heights, reverse=True)[0]
    return max_height

def display_name(tree, tree_name, tree_dir, outdir, full_taxon_dict, query_dict, label_fields):
    for k in tree.Objects:
        if k.branchType == 'leaf':
            name = k.name
            
            if "inserted" in name:
                collapsed_node_info = summarise_collapsed_node_for_label(tree_dir, outdir, name, tree_name, full_taxon_dict)
                k.traits["display"] = collapsed_node_info
            else:
                if name in full_taxon_dict:
                    taxon_obj = full_taxon_dict[name]
                
                    date = taxon_obj.sample_date
                    global_lineage = taxon_obj.global_lin
                    
                    k.traits["display"] = f"{name}|{date}|{global_lineage}"    

                    
                    if name in query_dict.keys():
                        if len(label_fields) > 0: 
                            for label_element in label_fields:
                                k.traits["display"] = k.traits["display"] + "|" + taxon_obj.attribute_dict[label_element]            
                
                else:
                    if name.startswith("subtree"):
                        number = name.split("_")[-1]
                        display = f"Tree {number}"
                        k.traits["display"] = display
                    else:
                        k.traits["display"] = name + "|" + "not in dict"


def find_colour_dict(query_dict, trait): 

    attribute_options = set()

    cmap = cm.get_cmap("Paired")

    if trait == "adm1": 
        colour_dict = {"NA": "#924242"}
        return colour_dict

    else:
        for query in query_dict.values():
            attribute_options.add(query.attribute_dict[trait])
            
    if len(attribute_options) == 2:
        colour_dict = {list(attribute_options)[0]: "#924242",
                        list(attribute_options)[1]:"#abbca3"}
        return colour_dict

    else:
        #get the right number of colours, then loop through the set
        colour_dict = {}
        count = 0
        colors = cmap(np.linspace(0, 1, len(attribute_options)))
        for option in attribute_options:
            colour_dict[option] = colors[count]
            count += 1
    
        return colour_dict


def make_scaled_tree(My_Tree, tree_name, tree_dir, outdir, num_tips, colour_dict_dict, colour_fields, label_fields, tallest_height,lineage, taxon_dict, query_dict):
#make colour_dict_dict optional argument
    display_name(My_Tree, tree_name, tree_dir, outdir, taxon_dict, query_dict, label_fields) 
    My_Tree.uncollapseSubtree()


    if num_tips < 10:
        #page_height = num_tips/2
        page_height = num_tips
    else:
        #page_height = num_tips/4 
        page_height = num_tips/2  

    offset = tallest_height - My_Tree.treeHeight
    space_offset = tallest_height/10
    absolute_x_axis_size = tallest_height+space_offset+space_offset + tallest_height #changed from /3 
    
    tipsize = 40
    c_func=lambda k: 'dimgrey' ## colour of branches
    l_func=lambda k: 'lightgrey' ## colour of branches
    s_func = lambda k: tipsize*5 if k.name in k.name in query_dict.keys() else tipsize
    z_func=lambda k: 100
    b_func=lambda k: 2.0 #branch width
    so_func=lambda k: tipsize*5 if k.name in k.name in query_dict.keys() else 0
    zo_func=lambda k: 99
    zb_func=lambda k: 98
    zt_func=lambda k: 97
    font_size_func = lambda k: 25 if k.name in k.name in query_dict.keys() else 15
    kwargs={'ha':'left','va':'center','size':12}

    if colour_fields != []:
        trait = colour_fields[0] #so always have the first trait as the first colour dot
        colour_dict = colour_dict_dict[trait]

        cn_func = lambda k: colour_dict[query_dict[k.name].attribute_dict[trait]] if k.name in query_dict.keys() else 'dimgrey'
        co_func=lambda k: colour_dict[query_dict[k.name].attribute_dict[trait]] if k.name in query_dict.keys() else 'dimgrey' 
        outline_colour_func = lambda k: colour_dict[query_dict[k.name].attribute_dict[trait]] if k.name in query_dict.keys() else 'dimgrey' 

    else:

        cn_func = lambda k: "#924242" if k.name in query_dict.keys() else 'dimgrey'
        co_func=lambda k: "#924242" if k.name in query_dict.keys() else 'dimgrey' 
        outline_colour_func = lambda k: "#924242" if k.name in query_dict.keys() else 'dimgrey' 

    x_attr=lambda k: k.height + offset
    y_attr=lambda k: k.y

    y_values = []
    for k in My_Tree.Objects:
        y_values.append(y_attr(k))
    min_y_prep = min(y_values)
    max_y_prep = max(y_values)
    vertical_spacer = 0.5 
    full_page = page_height + vertical_spacer + vertical_spacer
    min_y,max_y = min_y_prep-vertical_spacer,max_y_prep+vertical_spacer

    x_values = []
    for k in My_Tree.Objects:
        x_values.append(x_attr(k))
    max_x = max(x_values)
    
    
    fig,ax = plt.subplots(figsize=(20,page_height),facecolor='w',frameon=False, dpi=100)
    

    My_Tree.plotTree(ax, colour_function=c_func, x_attr=x_attr, y_attr=y_attr, branchWidth=b_func)
    My_Tree.plotPoints(ax, x_attr=x_attr, colour_function=cn_func,y_attr=y_attr, size_function=s_func, outline_colour=outline_colour_func)
    My_Tree.plotPoints(ax, x_attr=x_attr, colour_function=co_func, y_attr=y_attr, size_function=so_func, outline_colour=outline_colour_func)

    blob_dict = {}

    for k in My_Tree.Objects:
        
        if "display" in k.traits:
            name=k.traits["display"]

            x=x_attr(k)
            y=y_attr(k)
        
            height = My_Tree.treeHeight+offset
            text_start = tallest_height+space_offset+space_offset

            if len(colour_fields) > 1:
                
                division = (text_start - tallest_height)/(len(colour_fields))
                tip_point = tallest_height+space_offset

                if k.name in query_dict.keys():
                    
                    count = 0
                    
                    for trait in colour_fields[1:]:
                        
                        x_value = tip_point + count
                        count += division

                        option = query_dict[k.name].attribute_dict[trait]
                        colour_dict = colour_dict_dict[trait]
                        trait_blob = ax.scatter(x_value, y, tipsize*5, color=colour_dict[option])  
                        
                        blob_dict[trait] = x_value

                    ax.text(text_start+division, y, name, size=font_size_func(k), ha="left", va="center", fontweight="light")
                    if x != max_x:
                        ax.plot([x+space_offset,tallest_height],[y,y],ls='--',lw=1,color=l_func(k))

                else:

                    ax.text(text_start+division, y, name, size=font_size_func(k), ha="left", va="center", fontweight="light")
                    if x != max_x:
                        ax.plot([x+space_offset,tallest_height],[y,y],ls='--',lw=1,color=l_func(k))


                for blob_x in blob_dict.values():

                    line_x = blob_x - (division/2)

                    ax.plot([line_x,line_x],[min_y,max_y],ls='--',lw=3,color=l_func(k))
            
            
            else:
                ax.text(text_start, y, name, size=font_size_func(k), ha="left", va="center", fontweight="ultralight")
                ax.plot([x+space_offset,tallest_height+space_offset],[y,y],ls='--',lw=1,color=l_func(k))

    if len(colour_fields) > 1:

        blob_dict[colour_fields[0]] = tallest_height
        
        for trait, blob_x in blob_dict.items():

            y = max_y
            x = blob_x

            ax.text(x,y,trait, rotation=90, size=15,ha="center", va="bottom")

    if num_tips < 10:
        fig2,ax2 =  plt.subplots(figsize=(20,page_height/5),facecolor='w',frameon=False, dpi=200)
    else:
        fig2,ax2 =  plt.subplots(figsize=(20,page_height/10),facecolor='w',frameon=False, dpi=200)

    length = 0.00003

    ax2.plot([0,length], [0.5,0.5], ls='-', lw=1, color="dimgrey")
    ax2.text(0.000015,0.15,"1 SNP",size=20, ha="center", va="center")

    ax.spines['top'].set_visible(False) ## make axes invisible
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax2.spines['top'].set_visible(False) ## make axes invisible
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    ax2.spines['bottom'].set_visible(False)
    ax2.set_xticks([])
    ax2.set_yticks([])
    
    ax.set_xlim(-space_offset,absolute_x_axis_size)
    ax.set_ylim(min_y,max_y)
    ax2.set_xlim(-space_offset,absolute_x_axis_size)
    ax2.set_ylim(0,1)

    fig.tight_layout()


def sort_trees_index(tree_dir):
    b_list = []
    d_list = []
    for r,d,f in os.walk(tree_dir):
        for thing in f:
            if thing.endswith("tree"):
                a = thing.split(".")[0]
                b = a.split("_")[-1]
                b_list.append(int(b))
        
    c = sorted(b_list, key=int)
        
    return c

def make_all_of_the_trees(input_dir, outdir, tree_name_stem,taxon_dict, query_dict, colour_fields, label_fields, min_uk_taxa=3):

    tallest_height = find_tallest_tree(input_dir)

    too_tall_trees = []
    colour_dict_dict = defaultdict(dict)

    overall_df_dict = defaultdict(dict)

    overall_tree_count = 0
    
    lst = sort_trees_index(input_dir)

    for trait in colour_fields:
        colour_dict = find_colour_dict(query_dict, trait)
        colour_dict_dict[trait] = colour_dict

    for tree_number in lst:
        treename = f"tree_{tree_number}"
        treefile = f"{tree_name_stem}_{tree_number}.tree"
        nodefile = f"{tree_name_stem}_{tree_number}"
        num_taxa = 0

        tree = bt.loadNewick(input_dir + "/" + treefile, absoluteTime=False)

        old_node = tree.root
        new_node = bt.node()
        new_node.children.append(old_node)
        old_node.parent = new_node
        old_node.length=0.000015
        new_node.height = 0
        new_node.y = old_node.y
        tree.root = new_node

        tree.Objects.append(new_node)

        tips = []
        
        for k in tree.Objects:
            if k.branchType == 'leaf':
                tips.append(k.name)
        
        if len(tips) < 1000:

            df_dict = summarise_node_table(input_dir, nodefile, taxon_dict)

            overall_df_dict[treename] = df_dict

            overall_tree_count += 1     
        
            make_scaled_tree(tree, nodefile, input_dir, outdir, len(tips), colour_dict_dict, colour_fields, label_fields,tallest_height, tree_number, taxon_dict, query_dict)   
  
        else:
            too_tall_trees.append(tree_number)
            continue

    return too_tall_trees, overall_tree_count, overall_df_dict, colour_dict_dict

def summarise_collapsed_node_for_label(tree_dir, outdir, focal_node, focal_tree, full_tax_dict): 
    
    focal_tree_file = focal_tree + ".txt"
    warn_out = os.path.join(outdir, "tree_build_warnings.txt")
    with open(warn_out,"w") as f_warnings:
        with open(tree_dir + "/" + focal_tree_file) as f:
            next(f)
            for l in f:
                toks = l.strip("\n").split("\t")
                node_name = toks[0]
                members = toks[1]
            
                if node_name == focal_node:
                    summary_option = []
                    
                    member_list = members.split(",")
                    number_nodes = str(len(member_list)) + " nodes"

                    for tax in member_list:
                        if tax in full_tax_dict.keys():
                            taxon_obj = full_tax_dict[tax]
                            
                            summary_option.append(taxon_obj.node_summary)
                        
                        else: #should always be in the full metadata now
                            f_warnings.write(f"{tax} missing from full metadata\n")
                        
                    summary_counts = Counter(summary_option)

                    most_common_counts = []

                    if len(summary_counts) > 5:
                        
                        remaining = len(summary_counts) - 5
                        
                        most_common_tups = summary_counts.most_common(5)
                        for i in most_common_tups:
                            most_common_counts.append(i[0])

                        pretty_prep = str(most_common_counts).lstrip("[").rstrip("]").replace("'", "")
                        
                        if remaining == 1:
                            pretty = pretty_prep + " and " + str(remaining) + " other"
                        else:
                            pretty = pretty_prep + " and " + str(remaining) + " others"
                    
                    else:
                        pretty = str(list(summary_counts.keys())).lstrip("[").rstrip("]").replace("'", "")


                    node_number = node_name.lstrip("inserted_node")
                    pretty_node_name = "Collapsed node " + node_number

                    info = pretty_node_name + ": " + number_nodes + " in " + pretty

    return info

def summarise_node_table(tree_dir, focal_tree, full_tax_dict):

    focal_tree_file = focal_tree + ".txt"

    df_dict = defaultdict(list)

    with open(tree_dir + "/" + focal_tree_file) as f:
        next(f)
        for l in f:
            toks = l.strip("\n").split("\t")
            node_name = toks[0]
            members = toks[1]
        
            dates = []
            countries = []

            node_number = node_name.lstrip("inserted_node")
            
            member_list = members.split(",")

            for tax in member_list:
                if tax in full_tax_dict.keys():
                    taxon_obj = full_tax_dict[tax]
                
                    if taxon_obj.sample_date != "NA":
                        date_string = taxon_obj.sample_date
                        date = dt.datetime.strptime(date_string, "%Y-%m-%d").date()
                        dates.append(date)
                    
                    countries.append(taxon_obj.country)


            country_counts = Counter(countries)

            most_commons = country_counts.most_common(5)

            country_str = ""

            elem_count = 0

            for country, count in most_commons:
                elem_count += 1
                if elem_count == len(most_commons):
                    elem = country + " (" + str(count) + ")"
                    country_str += elem
                else:
                    elem = country + " (" + str(count) + "), "
                    country_str += elem
                
            if dates != []:
                min_date = str(min(dates))
                max_date = str(max(dates))
            else:
                min_date = "NA"
                max_date = "NA"

            size = len(member_list)

            df_dict["Node number"].append(node_number)
            df_dict["Number of sequences"].append(size)
            df_dict["Date range"].append(min_date + " to " + max_date)
            df_dict["Countries"].append(country_str)

    return df_dict

def make_legend(colour_dict):
    
    fig,ax = plt.subplots(figsize=(len(colour_dict)+1,1))

    plt.gca().set_aspect('equal', adjustable='box')
    plt.text
    
    x = 0
    for option in colour_dict.keys():
        circle = plt.Circle((x, 0.5), 0.05, color=colour_dict[option]) #((xloc, yloc), radius) relative to overall plot size
        ax.add_artist(circle)
        plt.text(x-0.1,0.3,option, fontsize=5)
        x += 1
        
        
    length = len(colour_dict)

    plt.xlim(-1,length)
    plt.ylim(0,1)

    ax.spines['top'].set_visible(False) ## make axes invisible
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)


    plt.yticks([])
    plt.xticks([])
    plt.show()

def describe_traits(full_tax_dict, node_summary, query_dict):

    trait_prep = defaultdict(list)
    trait_present = defaultdict(dict)

    for tax in full_tax_dict.values():
        if tax.tree != "NA" and tax not in query_dict.values():
            key = tax.tree 
            trait_prep[key].append(tax.node_summary)

    for tree, traits in trait_prep.items():
        counts = Counter(traits)
        trait_present[tree] = counts

    fig_count = 1
    tree_to_trait_fig = {}
    
    for tree, counts in trait_present.items():
        if len(counts) > 2:

            fig, ax = plt.subplots(1,1, figsize=(5,2.5), dpi=250)
            
            if len(counts) <= 5:
                sorted_counts = sorted(counts, key = lambda x : counts[x], reverse = True)
                x = list(sorted_counts)
                y = [counts[i] for i in x]
            elif len(counts) > 5:
                selected = sorted(dict(counts.most_common(10)), key = lambda x : counts[x], reverse = True)
                x = list(selected)
                y = [counts[i] for i in x]

            ax.bar(x,y, color="#924242")
            ax.set_xticklabels(x, rotation=90)
            ax.spines['top'].set_visible(False) ## make axes invisible
            ax.spines['right'].set_visible(False)
            ax.set_ylabel("Number of sequences")
            ax.set_xlabel(node_summary)
            
            tree_to_trait_fig[tree] = fig_count
            fig_count += 1


    return tree_to_trait_fig, trait_present
    


