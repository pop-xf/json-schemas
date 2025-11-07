# Specification of Fields in the `POPxf` JSON Format
A detailed specification of all fields in the proposed `POPxf` data format is given below. Each subsection describes the structure, expected data type, and allowed values of the corresponding entries in the `JSON` object. The data type *object* mentioned below refers to a `JSON` object literal and corresponds to a set of key/value pairs representing named subfields. The format is divided into two main components: the `metadata` and `data` fields. An additional `$schema` field is included to specify the version of the `POPxf` schema used. All quantities defined in this specification refer to a single datafile. They may be indexed by a superscript $(n)$ with $n \in [1,N]$ to denote quantities in a collection of $N$ datafiles. This is particularly relevant for discussing correlated predictions stored in separate files. Since this specification focuses on the format of a single datafile, we will omit the superscript $(n)$ to keep the notation concise. As a convention, we assume that all dimensionful quantities are given in units of GeV.

## `$schema` Field
The `$schema` field allows identifying a `JSON` file as conforming to the `POPxf` format and specifies the version of the `POPxf` schema used. It must be set to

`"https://json.schemastore.org/popxf-1.0.json"`

for files conforming to this version of the specification. The version number will be incremented for future revisions of the schema.

## `metadata` Field
The `metadata` field contains all contextual and structural information required to interpret the numerical predictions. It is a `JSON` object with the following subfields:

### `observable_names` (required, *type: array of string*)

Array of $M$ names identifying each observable. Must be an array of unique, non-empty strings, with at least one entry.

Example:

```json
  "observable_names": ["observable1", "observable2", "observable3"]
```

### `parameters` (required, *type: array of string*)

Array of model parameters (e.g., Wilson coefficient names) used in the polynomial expansion. Must be an array of unique, non-empty strings, with at least one entry.

Example:

```json
  "parameters": ["C1", "C2", "C3"]
```

### `basis` (required, *type: object*)

Defines the parameter basis (e.g. an operator basis in an EFT). At least one of the two subfields `wcxf` and `custom` has to be present. If both subfields are present, any element of `parameters` (see above) not belonging to the `wcxf` basis is interpreted as belonging to the `custom` basis. The subfields are defined as follows:

- **`wcxf` (optional, *type: object*)**: Specifies an EFT basis defined by the Wilson Coefficient exchange format (WCxf) [@Aebischer:2017ugx]. This object contains the following fields:
  - **`eft` (required, *type: string*)**: EFT name defined by WCxf (e.g., `"SMEFT"`)
  - **`basis` (required, *type: string*)**: Operator basis name defined by WCxf (e.g., `"Warsaw"`)
  - **`sectors` (optional, *type: array of string*)**: Array of renormalisation-group-closed sectors of Wilson coefficients containing the Wilson coefficients given in `parameters` (see above). The available sectors for each EFT are defined by WCxf.
- **`custom` (optional, *type: any*)**: Field of any type and substructure to unambiguously specify any parameter basis not defined by WCxf.

Example:

```json
  "basis": {
    "wcxf": {
      "eft": "SMEFT",
      "basis": "Warsaw",
      "sectors": ["dB=de=dmu=dtau=0"]
    }
  }
```

### `scale` (required, *type: number, array*)

The renormalisation scale in GeV at which the parameter vector $\vec{C}$ is defined. This field can take one of two forms:

- a single number, $\mu$: interpreted as the common scale for all observables. The polynomial expression for observable $O_m$ is understood to be a function of the parameters evolved to that common scale:

  $$O_m = a_m + \vec{C}(\mu) \cdot \vec{b}_m(\mu) + \dots\ $$

- an array of numbers, $\mu_m$: defining a separate scale for each observable. The array must have the same length $M$ as the array of observables. The polynomial expression for observable $O_m$ is understood to be a function of the parameters evolved to its corresponding scale:

  $$O_m = a_m + \vec{C}(\mu_m) \cdot \vec{b}_m(\mu_m) + \dots\ $$

  The array-of-numbers form is restricted in function-of-polynomials mode (see  Appendix A for details).

For a given observable, the observable coefficients ${\vec{o}_m \supset \vec{b}_m, \vec{c}_m, \dots}$ depend on the scale at which the parameters are defined, such that the observable itself is scale independent up to higher-order corrections in perturbation theory.

Examples:

```json
  "scale": 91.1876
```

```json
  "scale": [100.0, 200.0, 300.0, 400.0, 500.0]
```

### `polynomial_names` (optional, *type: array of string*)

*Required in function-of-polynomials mode.*

Array of names identifying the individual polynomials used in function-of-polynomials mode. Must contain unique, non-empty strings.

Example:

```json
  "polynomial_names": ["polynomial 1", "polynomial 2"]
```

### `observable_expressions` (optional, *type: array of object*)

*Required in function-of-polynomials mode.*

Defines how each observable is constructed from the named polynomials. Must be an array of $M$ objects, one per observable. The length and order of the array must match those of the `observable_names` field. Each object must contain:

- **`variables` (required, *type: object*)**: An object where each key is a string that is a Python-compatible variable name (used as variable in the `expression` field described below), and each value is a string identifying a polynomial name from `polynomial_names`. For example, `{"num": "polynomial 1", "den": "polynomial 2"}`.
- **`expression` (required, *type: string*)**: A Python-compatible mathematical expression using the dummy variable names defined in `variables`, e.g. `"num/den"`. Standard mathematical functions like `sqrt` or `cos` that are implemented in packages like `numpy` may be used.

Example:

```json
  "observable_expressions": [
    {
      "variables": {
        "num": "polynomial 1",
        "den": "polynomial 2"
      },
      "expression": "num / den"
    },
    {
      "variables": {
        "num": "polynomial 2",
        "den": "polynomial 1"
      },
      "expression": "num / den"
    },
    {
      "variables": {
        "p1": "polynomial 1"
      },
      "expression": "sqrt(p1**2)"
    }
  ]
```

### `polynomial_order` (optional, *type: integer*)

Specifies the maximum degree of polynomial terms included in the expansion. If omitted, the default value is 2 (i.e., quadratic polynomial). Values higher than 2 may be used to represent observables involving higher-order terms in the model parameters. The current implementation of the `JSON` schema defining the data format supports values up to 5. Higher orders are not prohibited in principle but are currently unsupported to avoid excessively large data structures.

Example:

```json
  "polynomial_order": 2
```

### `reproducibility` (optional, *type: array of object*)

Collects relevant data that may be required by a third party to reproduce the prediction. Each element of the array should be an object that corresponds to a step in the workflow and has three predefined fields: `description`, `tool` and `inputs`, specified below. In addition, any additional fields containing data deemed useful in this context can be included.

Schematic example:

```json
  "reproducibility": [
    {
      "description": "Description of the first step",
      "tool": { ... },
      "inputs": { ... }
    },
    {
      "description": "Description of the second step",
      "tool": { ... },
      "inputs": { ... }
    },
    ...
  ]
```
The predefined fields are as follows:

- **`description` (optional, *type: string*)**: Free-form text description of the method and tool used in this step of obtaining the predictions.
- **`inputs` (optional, *type: object*)**: Specifies the numerical values of input parameters used by the tool in producing the numerical values of the polynomial coefficients. Each entry maps an input name (a string) or a group of names (a stringified tuple such as `"('m1','m2')"`) to one of the following:
  - A single number: interpreted as the central value of a single, uncorrelated input parameter without uncertainty;
  - An object representing a uni- or multi-variate normal distribution describing one or more possibly correlated input parameters with uncertainties. This object can contain the subfields `mean`, `std`, and `corr`. If the key of the object is a stringified tuple of $N$ input names (e.g., `"('m1','m2')"` with $N = 2$), describing a group of $N$ possibly correlated input parameters, then `mean` and (if present) `std` must be arrays of length $N$, and (if present) `corr` must be an $N \times N$ matrix, expressed as an array of $N$ arrays of $N$ numbers. The subfields are defined as follows:
    - **`mean` (required, *type: ['number', 'array']*)**: central value / mean; a single number for a single input name, or an array of numbers for a group of input names;
    - **`std` (optional, *type: ['number', 'array']*)**: uncertainty / standard deviation; a single number for a single input name, or an array of numbers for a group of input names;
    - **`corr` (optional, *type: array of array*)**: correlation matrix; must only be used if a group of input names is given and requires the presence of `std`.
  - An object representing an arbitrary user-defined uni- or multi-variate probability distribution describing one or more input parameters. This object contains the following subfields:
    - **`distribution_type` (required, *type: string*)**: a user-defined name identifying the probability distribution (e.g. `"uniform"`);
    - **`distribution_parameters` (required, *type: object*)**: an object where each key is a user-defined name of a parameter of the probability distribution, and each value is a single number in the univariate case, or an array of numbers or arrays in the multivariate case (e.g. `{"a":0, "b":1}` for a uniform distribution with boundaries $a$ and $b$).
    - **`distribution_description` (required, *type: string*)**: Description of the custom distribution implemented, defining the fields in `distribution_parameters`.

  Example:

  In the example below, `"m1"` is an input parameter with no associated uncertainty, `"m2"` and `"m3"` are a pair of input parameters with correlated, Gaussian uncertainties, and `"m4"` is a parameter that is uniformly distributed between 0 and 1.

  ```json
    "inputs": {
      "m1": 1.0,
      "('m2','m3')": {
        "mean": [1.0, 2.0],
        "std": [0.1, 0.1],
        "corr": [
          [1.0, 0.3],
          [0.3, 1.0]
        ]
      },
      "m4": {
        "distribution_type": "uniform",
        "distribution_parameters": {
          "a": 0,
          "b": 1
        },
        "distribution_description": "Uniform distribution with boundaries $a$ and $b$."
      }
    }
  ```
- **`tool` (optional, *type: object*)**: Provides free-form information about the tool, software or technique used in a particular step of the workflow. The predefined subfields are `name`, `version`, and `settings`. Any number of additional fields may be included to record or link to supplementary metadata, such as model information/configuration, perturbative order, scale choice, PDF sets, simulation settings, input parameter cards, etc. The predefined subfields are as follows:
  - **`name` (required, *type: string*)**: name of tool, e.g. `"MadGraph5_aMC@NLO"`, `"POWHEG"`,  `"SHERPA"`, `"WHIZARD"`, `"flavio"`, `"FeynCalc"`, `"analytical calculation"`, ...
  - **`version` (optional, *type: string*)**: version of the tool, e.g. `"1.2"`
  - **`settings` (optional, *type: object*)**: object containing information about the tool settings with free-form substructure. For example:
      - `perturbative_order` (e.g. `"LO"`, `"NLO"`, `"NLOQCD"`, ...)
      - `PDF`: name, version, and set of the PDF used.
      - `UFO`: name and version of UFO model used, as well as any other relevant information such as flavor schemes or webpage link.
      - `scale_choice`: Nominal scale choice employed when computing the predictions. This could be an array of fixed scales or a string describing a dynamical scale choice like `"dynamical:HT/2"`. This field is particularly relevant when RGE effects are folded into the prediction, see the description of `metadata.scale` above.
      - `renormalization_scheme`: details of the renormalization scheme used in the computation.
      - `covariant_derivative_sign`: sign convention used for the covariant derivative (`"+"` or `"-"`).
      - `gamma5_scheme`: scheme used for $\gamma_5$ in dimensional regularization (`"BMHV"`, `"KKS"`, ...).
      - `evanescent`: details of the treatment of evanescent operators, e.g. a reference to the scheme used.
      - `approximations`: Any relevant approximations used, such as the use of the first leading-logarithmic approximation for RG evolution.
      - any other relevant settings specific to the tool or calculation.

  Examples:
  ```json
    "tool": {
      "name": "EFTTool",
      "version": "1.0.0"
    }
  ```

  ```json
    "tool": {
      "name": "MadGraph5_aMC@NLO",
      "version": "3.6.2",
      "settings": {
        "UFO": {
          "name": "SMEFTUFO",
          "version": "1.0.0",
          "webpage": "https://smeftufo.io"
        },
        "PDF": {
          "name": "LHAPDF",
          "version": "6.5.5",
          "set": "331700"
        },
        "perturbative_order": "NLOQCD",
        "scale_choice": [91.1876, 125.0]
      }
    }
  ```

  ```json
    "tool": {
      "name": "analytical calculation",
      "settings": {
        "gamma5_scheme": "KKS",
        "covariant_derivative_sign": "-",
        "renormalization_scheme": "MSbar (WCs), On-shell (mass, aS, aEW)",
        "evanescent": "https://doi.org/10.1016/0550-3213(90)90223-Z"
      }
    }
  ```

  ```json
    "tool": {
      "name": "RGEtool",
      "version": "1.0.0",
      "settings": {
        "perturbative_order": "one-loop",
        "method": "evolution matrix formalism"
      }
    }
  ```

### `misc` (optional, *type: object*)

Optional free-form metadata for documentation purposes. May include fields such as authorship, contact information, date, description of the observable, information identifying the associated correlation file (e.g. hash value or filename), or external references. The format is unrestricted, allowing any `JSON`-encodable content.

Example:

```json
  "misc": {
    "author": "John Doe",
    "contact": "john.doe@example.com",
    "description": "Example dataset",
    "URL": "johndoe.com/exampledata",
    "correlation_file": "correlations.json",
    "correlation_file_hash": "AB47BG3F11DA7DCAA5726008BAAFE176"
  }
```

## `data` Field
The `data` field contains the numerical representation of the observable predictions. This information is provided in terms of central values and uncertainties of polynomial coefficients, which are associated either directly with observables or with named polynomials on which the observables depend.

Each polynomial coefficient is labelled by a *monomial key*, written as a stringified tuple of model parameters (e.g., Wilson coefficients) defined in the `metadata` field `parameters`. For example, the key `"('C1', 'C2')":` corresponds to the monomial $C_1 C_2$. While the model parameters can be complex numbers, the polynomial coefficients are defined for the real and imaginary parts of the model parameters (see below) and are therefore strictly real. The format and conventions for monomial keys are as follows:

- Each key is a string representation of a Python-style tuple: a comma-separated array of strings enclosed in parentheses.
- The length of the tuple is determined by the polynomial order $k$, as defined by the  `metadata` field `polynomial_order` (default value: $k=2$, i.e. quadratic polynomial, if `polynomial_order` is omitted). The tuple length equals $k$, unless a real/imaginary tag is included (see below), in which case the length is $k+1$.
- The first $k$ entries in the tuple are model parameter names, as defined in the `metadata` field `parameters`. These names must be sorted alphabetically to ensure unique monomial keys (assuming the same sorting rules as Python's `sort()` method which sorts alphabetically according to ASCII or UNICODE-value, where upper case comes before lower case, and shorter strings take precedence). Empty strings `''` are used to represent constant terms (equivalent to $1$) and to pad monomials of lower degree. For example, for a quadratic polynomial in real parameters (see below for how complex parameters are handled):
  - A constant $1$ is written as `"('','')"`,
  - A linear term $C_1$ is written as `"('', 'C1')"`,
  - A quadratic term $C_1 C_2$ is written as `"('C1', 'C2')"`.
- To handle complex parameters, the tuple may optionally include a real/imaginary tag as its final element. This tag consists of `R` (real) and `I` (imaginary) characters, and its length must match the polynomial order $k$. It indicates whether each parameter refers to its real or imaginary part. For example:
  - `"('', 'C1', 'RI')"` corresponds to $\mathrm{Im}(C_1)$;
  - `"('C1', 'C2', 'IR')"` corresponds to $\mathrm{Im}(C_1)\,\mathrm{Re}(C_2)$.
- If the real/imaginary tag is omitted, the parameters are assumed to be real. For example:
  - `"('', 'C1')"` corresponds to $\mathrm{Re}(C_1)$;
  - `"('C1', 'C2')"` corresponds to $\mathrm{Re}(C_1)\,\mathrm{Re}(C_2)$.

These conventions ensure a canonical and unambiguous representation of polynomial terms while offering flexibility in the naming of model parameters. Missing monomials are implicitly treated as having zero coefficients.

 The `data` field is a `JSON` object with the following subfields:

### `observable_central` (optional, *type: object*)

An object representing the central values of the polynomial coefficients for the expanded observables, $\vec{o}_m$. Each key must be a monomial key as defined above. The values must be an array of $M$ numbers whose order matches `metadata.observable_names`.

Example:


Specifying three observable predictions, $O_{m}$, given in terms of the three real parameters $C_1$, $C_2$, and $C_3$ as

$$
\begin{aligned}
    O_1 &= 1.0 + 1.2 \ C_1 + 1.4 \ C_1C_2+ 1.6 \ C_1C_3\ , \\
    O_2 &= 1.1 + 1.3 \ C_1 + 1.5 \ C_1C_2+ 1.7 \ C_1C_3\ , \\
    O_3 &= 2.3 + 0.3\ C_1 + 0.7 \ C_1C_2 + 0.5 \ C_1C_3\ .
\end{aligned}
$$

```json
  "observable_central": {
    "('','')": [1.0, 1.1, 2.3],
    "('', 'C1')": [1.2, 1.3, 0.3],
    "('C1', 'C2')": [1.4, 1.5, 0.7],
    "('C1', 'C3')": [1.6, 1.7, 0.5]
  }
```

### `polynomial_central` (optional, *type: object*)

*Required in function-of-polynomials mode.*

An object representing the central values of the polynomial coefficients for each named polynomial, $\vec{p}_k$. Each key must be a monomial key as defined above. The values must be an array of $K$ numbers whose order matches `metadata.polynomial_names`.

Example:


Specifying two polynomials, $P_k$, given given in terms of two complex parameters $C_1$ and $C_2$ as

$$
\begin{aligned}
    P_1 &= 1.0 + 1.2 \ \mathrm{Im}(C_1) + 0.8 \ \mathrm{Re}(C_1) \mathrm{Re}(C_2) + 0.5 \ \mathrm{Re}(C_1) \mathrm{Im}(C_2)+ 0.2 \ \mathrm{Im}(C_1) \mathrm{Im}(C_2)\ , \\
    P_2 &= 1.1 + 1.3 \ \mathrm{Im}(C_1)  + 0.85 \ \mathrm{Re}(C_1) \mathrm{Re}(C_2) + 0.55 \ \mathrm{Re}(C_1) \mathrm{Im}(C_2)+ 0.25 \ \mathrm{Im}(C_1) \mathrm{Im}(C_2)\ .
\end{aligned}
$$

```json
  "polynomial_central": {
    "('','')": [1.0, 1.1],
    "('', 'C1', 'RI')": [1.2, 1.3],
    "('C1', 'C2', 'RR')": [0.8, 0.85],
    "('C1', 'C2', 'RI')": [0.5, 0.55],
    "('C1', 'C2', 'II')": [0.2, 0.25]
  }
```

### `observable_uncertainties` (optional, *type: object*)

An object representing the uncertainties on the polynomial coefficients for the expanded observables. The fields specify the nature of quoted uncertainty. In many cases there may only be a single top-level field, `"total"`, but multiple fields can be used to specify a breakdown into several sources of uncertainty (e.g., statistical, scale, PDF, ...). The values can either be an object or an array of floats. Objects must have the same structure as `observable_central`, arrays must have length $M$. If instead of an object, an array of floats is specified, it is assumed to correspond to the parameter independent uncertainty only (e.g. the uncertainty on the SM prediction). This would be equivalent to specifying an object with the single key, `"('', '')"`, matching the number of empty strings in the tuple to `metadata.polynomial_order`.

Examples:

```json
  "observable_uncertainties": {
    "total": {
      "('','')": [0.05, 0.06, 0.01],
      "('', 'C1')": [0.1, 0.12, 0.01],
      "('C1', 'C2')": [0.02, 0.03, 0.02],
      "('C1', 'C3')": [0.05, 0.06, 0.01]
    }
  }
```


Specifying only the SM uncertainties:

```json
  "observable_uncertainties": {
    "total": [0.05, 0.06, 0.01]
  }
```


Specifying an uncertainty breakdown:

```json
  "observable_uncertainties": {
    "MC_stats": {
      "('','')": [0.002, 0.0012, 0.001],
      "('', 'C1')": [0.001, 0.0015, 0.0001]
    },
    "scale": {
      "('','')": [0.04, 0.05, 0.06],
      "('', 'C1')": [0.1, 0.12, 0.01]
    },
    "PDF": {
      "('','')": [0.03, 0.04, 0.05],
      "('', 'C1')": [0.02, 0.08, 0.01]
    }
  }
```


Specifying a breakdown for SM uncertainties only:

```json
  "observable_uncertainties": {
    "MC_stats": [0.002, 0.0012, 0.001],
    "scale": [0.04, 0.05, 0.06],
    "PDF": [0.03, 0.04, 0.05]
  }
```
