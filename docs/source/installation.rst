Installation
============

Linux
-----

To get started on a Linux system:

#. **Install `virtualenv`** (if not already installed):

   .. code-block:: bash

      sudo apt install virtualenv

#. **Clone the repository:**

   .. code-block:: bash

      git clone git@github.com:phytec/phytec-eeprom-flashtool.git
      cd phytec-eeprom-flashtool

#. **Create and activate a virtual environment:**

   .. code-block:: bash

      virtualenv -p python3 venv
      source venv/bin/activate

#. **Install the tool and its dependencies:**

   .. code-block:: bash

      pip install .
      pip install -r requirements.txt

To deactivate the virtual environment, simply run:

.. code-block:: bash

   deactivate

Remember to re-activate the environment with ``source venv/bin/activate`` whenever you want to use the tool again.

Windows (PowerShell)
--------------------

To install the tool on Windows using PowerShell:

#. **Set the execution policy (once per user):**

   .. code-block:: powershell

      Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

#. **Clone the repository:**

   .. code-block:: powershell

      git clone git@github.com:phytec/phytec-eeprom-flashtool.git
      cd phytec-eeprom-flashtool

#. **Create and activate a virtual environment:**

   .. code-block:: powershell

      python -m venv venv
      .\venv\Scripts\Activate.ps1

#. **Install the tool and its dependencies:**

   .. code-block:: powershell

      pip install .
      pip install -r requirements-windows.txt

Without Virtual Environment (Not Recommended)
---------------------------------------------

While using a virtual environment is strongly recommended, the tool can also be installed system-wide:

#. **Clone the repository:**

   .. code-block:: bash

      git clone git@github.com:phytec/phytec-eeprom-flashtool.git
      cd phytec-eeprom-flashtool

#. **Install dependencies globally:**

   .. code-block:: bash

      pip install -r requirements.txt

#. **Run the tool from the repository root:**

   .. code-block:: bash

      python -m phytec_eeprom_flashtool
