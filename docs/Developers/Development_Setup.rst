Development Setup Notes
=======================

The following are some useful notes for setting up an environment to work on
coala.

Virtualenv
----------

We highly recommend installing coala in a virtualenv for development. This
will allow you to have a contained environment in which to modify coala,
separate from any other installation of coala that you may not want to break.
Here we will be showing how to have a virtualenv using :code:`venv` and
:code:`virtualenv`. We recommend using :code:`venv` as it is part
of the standard library and requires no extra installation. However,
you can use whichever you find suitable to yourself.

Using venv
~~~~~~~~~~

- Make sure to have Python 3 installed in your local machine.

- Setting up virtualenv with venv :
    ::

        $ cd working_dir # move into the dir where you want to create coala-venv
        $ python3 -m venv coala-venv
        # This creates an isolated Python 3 environment called coala-venv
        # in your current directory.
        # To activate the environment type:
        $ source coala-venv/bin/activate
        # To exit the environment simply type:
        (coala-venv)$ deactivate

- Now you can activate the environment and start
  `the next part <https://api.coala.io/en/latest/Developers/Development_Setup.html#repositories>`_.

Using virtualenv
~~~~~~~~~~~~~~~~

- Install virtualenv using pip3 :
    ::

        $ pip3 install virtualenv

- Create the virtualenv :
    ::

        $ cd working_dir # move into the dir where you want to create coala-venv
        $ virtualenv coala-venv

NOTE:
If you have both Python 3 and Python 2 installed try this command
it creates an isolated Python 3 environment called coala-venv
in your current directory, as coala only works for Python >= 3.5
::

    $ virtualenv coala-venv -p $(which python3)

- Activate the *coala-venv* isolated environment :

    + If you are a Linux or Mac user:

    ::

        $ source coala-venv/bin/activate
        (coala-venv)$ deactivate # to exit the environment

    + And if you are a Windows user:

    ::

        > coala-venv\Scripts\activate
        (coala-venv)> deactivate # to exit the environment

- If you run into any hiccups refer to the
  `Virtualenv User Guide <https://virtualenv.pypa.io/en/latest/user_guide.html#activators>`__.

- After this, you can start
  `installing from git <https://api.coala.io/en/latest/Developers/Development_Setup.html#installing-from-git>`__.

Repositories
------------

If you are interested in contributing to coala, we recommend that you read
our `newcomers' guide <http://api.coala.io/en/latest/Developers/Newcomers_Guide.html>`__
to familiarize yourself with our workflow, and perhaps with GitHub itself.

You will most likely need to work only in the ``coala`` or ``coala-bears``
repository. The former is the core of coala, and the latter contains the set
of standard bears. You can fork and clone the repositories from:

https://github.com/coala/coala

https://github.com/coala/coala-bears

Beside those repositories above, ``package_manager`` and ``coala-utils``
are fundamental parts of coala which is hosted on GitLab.

https://gitlab.com/coala/package_manager/

https://gitlab.com/coala/coala-utils/

Installing from Git
-------------------

We recommend installing coala and coala-bears from the master branch for
latest updates and its dependencies with pip3 using the commands given below.
The ``-e`` tag installs the project in the editable mode from the given path.

::

    (coala-venv)$ git clone https://github.com/coala/coala
    (coala-venv)$ cd coala
    (coala-venv)$ pip3 install -e .
    (coala-venv)$ cd ..
    (coala-venv)$ git clone https://github.com/coala/coala-bears
    (coala-venv)$ cd coala-bears
    (coala-venv)$ pip3 install -e .

You will then be able to edit the repository and have the changes take effect
in your virtualenv immediately. You will also be able to use pip3 to manage
your installation of the package should you need to install from a different
source in the future.


Building Documentation
----------------------

You should run this command before trying to build the documentation:

::

    (coala-venv)$ pip3 install -r docs-requirements.txt

Once you have done so, you can build the documentation by entering the docs
directory and running ``python3 setup.py docs``. The documentation
on the coala website is in
the ``coala`` (not ``coala-bears``) repository.
