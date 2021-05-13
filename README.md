# Data Generation with Blender

This repository contains Blender code and external scripts using it to render data from recently available 3D datasets like:

- Matterport3D
- Stanford2D3D
- GibsonV2
- SunCG (now discontinued)

The generated data are not necessarily purely synthetic (except for the case of SunCG), as the 3D models are the result of scanning interior spaces with the Matterport camera.
While the datasets themselves offer the Matterport camera partial views (perspective or panorama), there are pros and cons for using those or the rendered ones.

## TODOs:

- [ ] Data conversion scripts
- [ ] Documentation
- [ ] Examples

## Documentation
The code and scripts are unfortunately currently undocumented.

## Citation

The code and scripts in this repository have been used in the context of various works requiring data generation with Blender.
If you find this useful in your work please consider citing on of them:

```
@inproceedings{albanis2021pano3d,
  author       = "Albanis, Georgios and Zioulis, Nikolaos and Drakoulis, Petros and Gkitsas, Vasileios and Strezentsenko, Vladimiros and Alvarez, Federico and Zarpalas, Dimitrios and Daras, Petros",
  title        = "Pano3D: A Holistic Benchmark and a Solid Baseline for \360 Depth Estimation",
booktitle = {Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR) Workshops},
month = {June},
year = {2021}
}
```

```
@inproceedings{albanis2020dronepose,
  author       = "Albanis, Georgios and Zioulis, Nikolaos and Dimou, Anastasios and Zarpalas, Dimitris and Daras, Petros",
  title        = "DronePose: Photorealistic UAV-Assistant Dataset Synthesis for 3D Pose Estimation via a Smooth Silhouette Loss",
  booktitle    = "European Conference on Computer Vision Workshops (ECCVW)",
  month        = "August",
  year         = "2020"
}
```

```
@inproceedings{zioulis2019spherical,
  author       = "Zioulis, Nikolaos and Karakottas, Antonis and Zarpalas, Dimitris and Alvarez, Federic and Daras, Petros",
  title        = "Spherical View Synthesis for Self-Supervised $360^o$ Depth Estimation",
  booktitle    = "International Conference on 3D Vision (3DV)",
  month        = "September",
  year         = "2019"
}
```

```
 @inproceedings{karakottas2019360surface,
        author      = "Karakottas, Antonis and Zioulis, Nikolaos and Samaras, Stamatis and Ataloglou, Dimitrios and Gkitsas, Vasileios and Zarpalas, Dimitrios and Daras, Petros",
        title       = "360 Surface Regression with a Hyper-Sphere Loss",
        booktitle   = "International Conference on 3D Vision (3DV)",
        month       = "September",
        year        = "2019"
      }
```

```
@inproceedings{zioulis2018omnidepth,
  title={Omnidepth: Dense depth estimation for indoors spherical panoramas},
  author={Zioulis, Nikolaos and Karakottas, Antonis and Zarpalas, Dimitrios and Daras, Petros},
  booktitle={Proceedings of the European Conference on Computer Vision (ECCV)},
  pages={448--465},
  year={2018}
}
```