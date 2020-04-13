# shape_finder

Find shapes in the image

## Grabbing the code
```
git clone https://github.com/...
```

## Setup requirements
Install all requirements:
```
pip install -r requirements.txt
```

## Running application
```
python shape_finder.py -s shapes_file_name -i image_name
```
where

* `shapes_file_name` - shapes file name, e.g. `input.txt`
* `image_name` - image name, e.g. `image.png`

### Input

#### Shapes file

Shapes file should contain:

* number `N` - shapes number
* `N` lines with coordinates `X`, `Y` of shapes vertexes

E.g.:

```
2
0, 0, 1, 1, 1, 0
0, 0, 0, 1, 1, 1, 1, 0
```

#### Image

![Image](image.png)

### Output

Output contains:

* number `M` - number of detected primitives
* `M` lines with transformations: shape number, bias `X`, bias `Y`, scale and rotation angle

E.g.:

```
3
1, 119, 196, 50, 231
0, 128, 82, 79, 150
1, 163, 78, 58, -61
```
