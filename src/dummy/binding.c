#include <stdio.h>
#include <Python.h>
#include "libavcodec/avcodec.h"
#include "libavdevice/avdevice.h"
#include "libavfilter/avfilter.h"
#include "libavformat/avformat.h"

#define MODULE_NAME "dummy.binding"

static PyObject*
test(PyObject *Py_UNUSED(self), PyObject *Py_UNUSED(ignored))
{
    const AVFilter *libvmaf;
    AVFilterContext *libvmaf_context;
    AVFilterGraph *graph;

    // initialise libraries
    avformat_network_init();
    avdevice_register_all();

    libvmaf = avfilter_get_by_name("libvmaf");
    if (libvmaf == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FFmpeg libvmaf filter is unavailable");
        return NULL;
    }

    graph = avfilter_graph_alloc();
    if (graph == NULL) {
        return PyErr_NoMemory();
    }
    if (avfilter_graph_create_filter(
            &libvmaf_context, libvmaf, "libvmaf", NULL, NULL, graph) < 0) {
        avfilter_graph_free(&graph);
        PyErr_SetString(
            PyExc_RuntimeError,
            "FFmpeg libvmaf filter initialization failed"
        );
        return NULL;
    }
    avfilter_graph_free(&graph);

    fprintf(stderr, "FFmpeg with libvmaf is OK\n");

    Py_RETURN_NONE;
}

static PyMethodDef module_methods[] = {
    {"test", (PyCFunction)test, METH_NOARGS, ""},
    {NULL}
};

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    MODULE_NAME,                        /* m_name */
    "Dummy bindings for FFmpeg.",       /* m_doc */
    -1,                                 /* m_size */
    module_methods,                     /* m_methods */
    NULL,                               /* m_reload */
    NULL,                               /* m_traverse */
    NULL,                               /* m_clear */
    NULL,                               /* m_free */
};

PyMODINIT_FUNC
PyInit_binding(void)
{
    PyObject* m;

    m = PyModule_Create(&moduledef);
    if (m == NULL)
        return NULL;

    return m;
}
