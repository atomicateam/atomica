.. title:: Atomica

.. image:: atomica_logo.png
    :scale: 70%
    :align: center


[Atomica](https://https://github.com/atomicateam/atomica) is a simulation engine for compartmental models. It can be used to simulate disease epidemics, health care cascades, and many other things.

To install via PyPI:

.. code-block:: python

    pip install atomica

You can run a plot an Atomica demo with:

.. code-block:: python

    import atomica as at
    import matplotlib.pyplot as plt

    P = at.demo("sir")
    d = at.PlotData(P.results[0], project=P)
    figs = at.plot_series(d)
    plt.show()

.. toctree::
    :maxdepth: 1

    general/index
    examples/index
    tutorial/index
    library/index

.. autosummary::
   :toctree: _autosummary
   :caption: API Reference
   :template: custom-module-template.rst
   :recursive:

   atomica
