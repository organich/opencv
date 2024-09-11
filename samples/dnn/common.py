import sys
import os
import cv2 as cv


def add_argument(zoo, parser, name, help, required=False, default=None, type=None, action=None, nargs=None, alias=None):
    if alias is not None:
        modelName = alias
    elif len(sys.argv) > 1:
        modelName = sys.argv[1]
    else:
        return

    if os.path.isfile(zoo):
        fs = cv.FileStorage(zoo, cv.FILE_STORAGE_READ)
        node = fs.getNode(modelName)
        if not node.empty():
            value = node.getNode(name)
            if "sha1" in name:
                prefix = name.replace("sha1", "")
                value = node.getNode(prefix + "load_info")
                value = value.getNode(name)
            if "download_sha" in name:
                prefix = name.replace("download_sha", "")
                value = node.getNode(prefix + "load_info")
                value = value.getNode(name)
            if not value.empty():
                if value.isReal():
                    default = value.real()
                elif value.isString():
                    default = value.string()
                elif value.isInt():
                    default = int(value.real())
                elif value.isSeq():
                    default = []
                    for i in range(value.size()):
                        v = value.at(i)
                        if v.isInt():
                            default.append(int(v.real()))
                        elif v.isReal():
                            default.append(v.real())
                        else:
                            print('Unexpected value format')
                            exit(0)
                else:
                    print('Unexpected field format')
                    exit(0)
                required = False

    if action == 'store_true':
        default = 1 if default == 'true' else (0 if default == 'false' else default)
        assert(default is None or default == 0 or default == 1)
        parser.add_argument('--' + name, required=required, help=help, default=bool(default),
                            action=action)
    else:
        parser.add_argument('--' + name, required=required, help=help, default=default,
                            action=action, nargs=nargs, type=type)


def add_preproc_args(zoo, parser, sample, alias=None, prefix=""):
    aliases = []
    if os.path.isfile(zoo):
        fs = cv.FileStorage(zoo, cv.FILE_STORAGE_READ)
        root = fs.root()
        for name in root.keys():
            model = root.getNode(name)
            if model.getNode('sample').string() == sample:
                aliases.append(name)

    parser.add_argument(prefix+'alias', nargs='?', choices=aliases,
                        help='An alias name of model to extract preprocessing parameters from models.yml file.')
    add_argument(zoo, parser, prefix+'model',
                 help='Path to a binary file of model contains trained weights. '
                      'It could be a file with extensions .caffemodel (Caffe), '
                      '.pb (TensorFlow), .weights (Darknet), .bin (OpenVINO)', alias=alias)
    add_argument(zoo, parser, prefix+'config',
                 help='Path to a text file of model contains network configuration. '
                      'It could be a file with extensions .prototxt (Caffe), .pbtxt or .config (TensorFlow), .cfg (Darknet), .xml (OpenVINO)', alias=alias)
    add_argument(zoo, parser, prefix+'mean', nargs='+', type=float, default=[0, 0, 0],
                 help='Preprocess input image by subtracting mean values. '
                      'Mean values should be in BGR order.', alias=alias)
    add_argument(zoo, parser, prefix+'std', nargs='+', type=float, default=[0, 0, 0],
                 help='Preprocess input image by dividing on a standard deviation.', alias=alias)
    add_argument(zoo, parser, prefix+'scale', type=float, default=1.0,
                 help='Preprocess input image by multiplying on a scale factor.', alias=alias)
    add_argument(zoo, parser, prefix+'width', type=int,
                 help='Preprocess input image by resizing to a specific width.', alias=alias)
    add_argument(zoo, parser, prefix+'height', type=int,
                 help='Preprocess input image by resizing to a specific height.', alias=alias)
    add_argument(zoo, parser, prefix+'rgb', action='store_true',
                 help='Indicate that model works with RGB input images instead BGR ones.', alias=alias)
    add_argument(zoo, parser, prefix+'labels',
                 help='Optional path to a text file with names of labels to label detected objects.', alias=alias)
    add_argument(zoo, parser, prefix+'postprocessing', type=str,
                 help='Post-processing kind depends on model topology.', alias=alias)
    add_argument(zoo, parser, prefix+'background_label_id', type=int, default=-1,
                 help='An index of background class in predictions. If not negative, exclude such class from list of classes.', alias=alias)
    add_argument(zoo, parser, prefix+'sha1', type=str,
                 help='Optional path to hashsum of downloaded model to be loaded from models.yml', alias=alias)
    add_argument(zoo, parser, prefix+'download_sha', type=str,
                 help='Optional path to hashsum of downloaded model to be loaded from models.yml', alias=alias)

def findModel(filename, sha1):
    if filename:
        if os.path.exists(filename):
            return filename

        fpath = cv.samples.findFile(filename, False)
        if fpath:
            return fpath

        if os.getenv('OPENCV_DOWNLOAD_CACHE_DIR') is None:
            print('[WARN] Please specify a path to model download directory in OPENCV_DOWNLOAD_CACHE_DIR environment variable.')
            return findFile(filename)

        if os.path.exists(os.path.join(os.environ['OPENCV_DOWNLOAD_CACHE_DIR'], sha1, filename)):
            return os.path.join(os.environ['OPENCV_DOWNLOAD_CACHE_DIR'], sha1, filename)

        if os.path.exists(os.path.join(os.environ['OPENCV_DOWNLOAD_CACHE_DIR'], filename)):
            return os.path.join(os.environ['OPENCV_DOWNLOAD_CACHE_DIR'], filename)

    raise FileNotFoundError('File ' + filename + ' not found! Please specify a path to '
            'model download directory in OPENCV_DOWNLOAD_CACHE_DIR '
            'environment variable or pass a full path to ' + filename)

def findFile(filename):
    if filename:
        if os.path.exists(filename):
            return filename

        fpath = cv.samples.findFile(filename, False)
        if fpath:
            return fpath

        if os.getenv('OPENCV_SAMPLES_DATA_PATH') is None:
            print('[WARN] Please specify a path to `/samples/data` in OPENCV_SAMPLES_DATA_PATH environment variable.')
            exit(0)

        if os.path.exists(os.path.join(os.environ['OPENCV_SAMPLES_DATA_PATH'], filename)):
            return os.path.join(os.environ['OPENCV_SAMPLES_DATA_PATH'], filename)

        for path in ['OPENCV_DNN_TEST_DATA_PATH', 'OPENCV_TEST_DATA_PATH', 'OPENCV_SAMPLES_DATA_PATH']:
            try:
                extraPath = os.environ[path]
                absPath = os.path.join(extraPath, 'dnn', filename)
                if os.path.exists(absPath):
                    return absPath
            except KeyError:
                pass

    raise FileNotFoundError(
        'File ' + filename + ' not found! Please specify the path to '
        '/opencv/samples/data in the OPENCV_SAMPLES_DATA_PATH environment variable, '
        'or specify the path to opencv_extra/testdata in the OPENCV_DNN_TEST_DATA_PATH environment variable, '
        'or specify the path to the model download cache directory in the OPENCV_DOWNLOAD_CACHE_DIR environment variable, '
        'or pass the full path to ' + filename + '.'
    )


def get_backend_id(backend_name):
    backend_ids = {
        "default": cv.dnn.DNN_BACKEND_DEFAULT,
        "openvino": cv.dnn.DNN_BACKEND_INFERENCE_ENGINE,
        "opencv": cv.dnn.DNN_BACKEND_OPENCV,
        "vkcom": cv.dnn.DNN_BACKEND_VKCOM,
        "cuda": cv.dnn.DNN_BACKEND_CUDA
    }

    if backend_name not in backend_ids:
        raise ValueError(f"Invalid backend name: {backend_name}")

    return backend_ids[backend_name]

def get_target_id(target_name):
    target_ids = {
        "cpu": cv.dnn.DNN_TARGET_CPU,
        "opencl": cv.dnn.DNN_TARGET_OPENCL,
        "opencl_fp16": cv.dnn.DNN_TARGET_OPENCL_FP16,
        "ncs2_vpu": cv.dnn.DNN_TARGET_MYRIAD,
        "hddl_vpu": cv.dnn.DNN_TARGET_HDDL,
        "vulkan": cv.dnn.DNN_TARGET_VULKAN,
        "cuda": cv.dnn.DNN_TARGET_CUDA,
        "cuda_fp16": cv.dnn.DNN_TARGET_CUDA_FP16
    }
    if target_name not in target_ids:
        raise ValueError(f"Invalid target name: {target_name}")

    return target_ids[target_name]