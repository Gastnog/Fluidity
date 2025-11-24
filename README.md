# Fluidity

Algorithm to infer Traffic Light Rhythms from GPS Positioning Data.

Author: Gaston Laplagne
Creation Date: 17/11/2025
Abstract
This document describes a machine learning approach to infer traffic light timing patterns using GPS data from urban mobility. By analyzing the stop-and-go patterns of vehicles across city networks, we aim to reconstruct traffic light cycles without physical sensors or municipal cooperation, enabling better traffic optimization.
Once traffic lights' rhythms are learned, the goal is to return this information to drivers so they can adapt their driving to the future state of the traffic light.
This document describes the first steps of this project.

1. Problem Statement

1.1 Context

As soon as two streets needed to intersect, the traffic light quickly became the standard solution worldwide to facilitate the crossing of two traffic lanes. Our journeys are therefore punctuated with somewhat archaic traffic control devices, which we obey without really knowing what's happening inside these black, illuminated boxes.

Urban congestion represents a major challenge for modern cities, with significant economic, environmental, and social impacts. Traffic lights, while necessary, often contribute to congestion when not optimized for actual traffic flows.


The technical principle : With GPS Positioning Data of vehicles, write an algorithm that calculate the traffic light rhythms.

So in the following steps we inform drivers of the status of the next traffic light on their route, allowing them to drive more fuel-efficiently.

Examples:

Avoiding unnecessary acceleration towards a green light that turns red/orange at the last second.

Optimizing the approach speed when passing through a traffic light that appears red in the distance.

Optimizing engine shutdown during extended stops and making it easier to anticipate when to restart the engine before departure.

Anticipating a traffic light going to green to eliminate the reaction time from green light to acceleration/departure. 

1.2 Opportunities / Difficulties

Opportunity : 
Traffic lights are mostly programmed locally, and no centralized command exists for them. Thus the information about their rhythms is hard to find with physical sensors.


The proliferation of smartphones and GPS devices offers a rich source of mobility data to help understand urban traffic light dynamics.


Autonomous vehicles and smart cities would also benefit from traffic light information.

Difficulties : 
Complex Machine Learning algorithms are required.
Intersection type recognition.
Vehicle positions and speeds analysis.
Traffic light positioning.


Models need to be designed and trained using simulation.
Data are hard to get from real applications like Waze, Google Maps, Mappy or others.
A significant amount of data is required per traffic light.


Some intersections are equipped with some pedestrian priority buttons.
Some traffic lights are adjustable for traffic management. It will be impossible to learn a fixed rhythm with this kind of system.


2. Methodological Proposal

2.1 Simulation to generate vehicle data.

To develop an algorithm that learns traffic light timings, various software options are available. SUMO (Simulation of Urban MObility) meets our needs to generate vehicle data.

About SUMO.
Native handling of traffic lights with customizable timing.
Easy export of vehicle position data.
Python API for machine learning integration.
Active community and comprehensive documentation.
With this simulation tool 
Set up a single way road with a traffic light.
Set traffic light rhythms.
Design a vehicle flow that obeys this traffic light.
Record the position and speed of the vehicles that pass through this traffic light.
2.2 Analytic phase to find traffic light timers.
The data, once generated with SUMO, results in a CSV file that should be treated with tools like R, Python, Matlab, Pandas or other data processing software to calculate the traffic light rhythms.

2.2 Algorithm basis.

The algorithm has to calculate the traffic light timers.


Time red
Time green
Real-Time offset of

This will be done with the analysis of the vehicle speed curves generated.
A car that is stopped before the traffic light and then starts accelerating means the traffic light turned from red to green.
A car that stops before the traffic light indicates that it started to brake when the traffic light turned from green to red.
To validate the algorithm it needs to find the traffic light timers set in the simulation with SUMO.

So in all the speed curves generated with a vehicle flow going through a traffic light, we are insterested in analysing the speed curve of vehicules that stops just before the traffic light position (x,y)

Time red = t(starts accelerating) - t(started to break)
For red the two times will be from the same vehicule)

And Time green = t(next vehicle starting to break) - t(first vehicle start accelerating)
For green we need 2 vehicles, the first accelerating and the next that start Breaking before the traffic light.

3 Conclusion and Perspectives.

This document describes a central, albeit small, component of a project that includes time-series analysis, clustering, supervised learning, and anomaly detection. These methods aim to uncover recurring patterns in vehicle speed and position data, enabling the reconstruction of traffic light cycles.
Nevertheless, significant challenges remain. Access to real-world GPS data is limited by privacy concerns, API restrictions, traffic lights detection, unexpected drivers behaviors, managing large and noisy datasets, and complex urban intersections add layers of difficulty.
Despite all this, the potential benefits are real. By providing drivers with real-time insights into traffic light behavior, this approach could optimize fuel efficiency, reduce emissions, improve traffic flow, reduce time spent in transport, and even adjust the red-green ratio of traffic lights according to the busiest lanes.
Looking ahead, future work will focus on validating the algorithm with real-world data,and refining the models.

