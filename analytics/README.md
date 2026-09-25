# Module 2-Analytics Pipeline

## What I did in this module:

In this module I worked with the classic Titanic dataset. First I looked at the data closely to understand it (this is called EDA - Exploratory Data Analysis), cleaned up the messy parts, and made some charts with my own explanation under each one. After that, I built machine learning models that try to guess if a passenger survived or not, checked how good each model is, and picked the best one to save for later use. I split the work into two notebooks that run one after another.

- **`01_eda.ipynb`** gets the data, looks at it, cleans it, saves a copy as `titanic.csv`, and makes the charts with explanations.
- **`02_modeling.ipynb`** opens that same `titanic.csv` file and does all the model building and testing. It does not download the data again.

## What was expected

- Load the Titanic dataset and save it as a CSV file so it still works even without internet later. Look at missing values and decide what to do with them using clear rules (drop, fill in, or something else), and say why for each one. Make charts (histogram, box plot, comparisons, a correlation heatmap) with a short explanation under each - at least 4 charts in total, all explained, not just shown. Split the data into train and test sets the right way (using stratify) before doing any cleaning on it, so the test data stays "unseen".
- Build 3 models: Logistic Regression, Decision Tree, and Random Forest and compare them using accuracy, precision, recall, F1 score, and ROC-AUC. Handle the fact that more people died than survived (class imbalance) using SMOTE and/or class_weight. Tune the Random Forest model using GridSearchCV and get its OOB (out-of-bag) score. Also build a simple regression model to predict the ticket fare, and check its errors.
- Save the finished model (cleaning steps + model together) using `joblib`, so it can be reloaded and used again on new data.

## What I got in the end

- All the missing value percentages were measured and each one was handled with a clear reason (see the table below). 4 clear charts, each with in 2 to 4 sentences explaining what it means, plus a correlation heatmap. All 3 models trained on the exact same train/test split, compared side by side in one table.
- A tuned Random Forest with its best settings and OOB score printed out. A working comparison of 3 ways to handle class imbalance (do nothing, class_weight, SMOTE). A regression model for fare with MAE, RMSE, R², and Adjusted R² all reported.
- A single saved file (titanic_pipeline.joblib) that has both the cleaning steps and the model together, which I reloaded and tested on brand new, raw passenger data to make sure it still works.

## How to set it up and run it

```bash
python -m venv .venv
.venv\Scripts\activate 
pip install -r analytics/requirements.txt
```

To run everything from start to finish:

```bash
cd analytics
jupyter nbconvert --to notebook --execute --inplace 01_eda.ipynb
jupyter nbconvert --to notebook --execute --inplace 02_modeling.ipynb
```

(or we can just open both files in Jupyter/VS Code and run every cell from top to bottom.)

---

## Problems I faced while doing this module.

Some columns had a lot of missing values (like deck, which was missing more than 77% of the time), while others had just a couple of missing rows (embarked, embark_town) and its confusing. As per the points mentioned in project, If less than 5% is missing, I have droped those rows since it's only a tiny loss, if between 5% and 30% is missing filled it in (impute) using something like the middle value and if way more than 30% is missing, dropped the whole column. For deck, I chose to drop the whole column, because with over 3 out of 4 values missing, guessing them would just add noise, and the ticket class/fare columns already tell a similar story.

At first I was thought to clean the data once and use that same cleaned version everywhere. Then later after going through all the points in requirement I kept two separate cleaning processes one simple one just for making charts and understanding the data, and the other one inside the model pipeline that is only ever fit on the training part of the data.

After running the hyperparameter tuning step (GridSearchCV), I sometimes saw a error message printing out at the very end, mentioning something about "resource_tracker" and "joblib". After realising and learning about that error, I left the setting as it was since it does not cause any real problem as it was just a warning message.

When I first tuned the Random Forest, I tried to read its oob_score_ value and got an error saying it wasn't available. I found out that Random Forest only calculates this score if you tell it to when you first create the model, using oob_score=True. I had forgotten to add this setting the first time. After adding that when building the model, the OOB score showed up correctly.

---

## Part A-Looking at and cleaning the data (`01_eda.ipynb`)

### Missing value strategy (exact percentages measured, threshold rule applied as per rules explained)

| Column          | % missing | What I did                 | Why                                                                                                                |
| --------------- | --------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `deck`        | 77.22%    | **Drop column**      | Way too much missing to fill in reliably.pclass/fare already tell a similar story about a passenger's cabin area. |
| `age`         | 19.87%    | **Fill in (median)** | This is in the 5-30% range, so filling it in with the middle value is a safe, standard choice.                     |
| `embarked`    | 0.22%     | **Drop rows**        | It is under 5% missing, and only 2 rows, so dropping them loses almost nothing.                                   |
| `embark_town` | 0.22%     | **Drop rows**        | Same 2 rows as embarked (they are missing together).                                                               |

### Outliers and skew

- Using the IQR rule (a common way to spot unusual values): age has **65 outliers**, fare has **114 outliers**. For fare, mean = 32.10, median = 14.45, mode = 8.05. As per my histogram and box plot for fare, the shape is not even/symmetric  as it has a long tail stretching to the right. Since mean is bigger than median, which is bigger than mode, I concluded fare is right-skewed which shows most people paid a low fare, but a few people (mostly 1st class) paid a lot, and those big numbers pull the average up higher than the typical (median) value.

### Survival rates by group (using boolean masking)

| Group             | Survival rate |
| ----------------- | ------------- |
| Male              | 18.9%         |
| Female            | 74.0%         |
| Pclass 1          | 62.6%         |
| Pclass 2          | 47.3%         |
| Pclass 3          | 24.2%         |
| Female + Pclass 1 | 96.7%         |
| Male + Pclass 3   | 13.5%         |

### Correlation matrix (6 number columns only)

I only used survived, pclass, age, sibsp, parch, fare for this (leaving out adult_male and alone since they're just derived from other columns, not new information). As per my heatmap, most boxes are a light colour (close to 0), meaning most pairs of columns don't move together much. The two darkest, strongest boxes on my heatmap were:

1. pclass and fare: r = -0.55 - this is the darkest box on my heatmap. It makes sense, since ticket class is directly tied to how much you pay and lower class number (1st class) means a higher fare.
2. sibsp and parch: r = +0.41 - the second darkest box. Both of these columns are about travelling with family, so it makes sense they move together.

### The data story with 4 charts, each explained

1. Survival by class and sex (bar chart): As per my graph, being female and being in a higher class both help a lot on their own, and together they help even more: I can see female survival at 92% or higher in 1st/2nd class, while male survival drops to just 13-16% outside 1st class. This tells me sex and class are not two separate small effects, they stack on top of each other.
2. Age vs survival (box plot): Looking at my graph, the typical age (the middle line in the box) is close for both survivors and non-survivors. But I can see more very young children sitting among the survivors, which matches the "children first" idea. Outside of early childhood though, my graph shows age alone doesn't separate the two groups much.
3. Fare vs survival (distribution plot):From my graph, I can see that passengers who survived tended to have paid a bit more for their ticket, shown by their curve sitting slightly to the right. This lines up with the class pattern from chart 1, just shown through a different number (fare instead of class label).
4. Survival by family size (bar chart): This graph gave me the most surprising result, since it is not a straight line, travelling alone gives 30.4% survival, having a small family (1-3 people) gives the best result at 57.9%, but a large family (4+) drops back down to only 16.1%. So as per my graph, having a small family with you seems to have helped the most, more than being alone or being in a big group.

### Quick check: standardizing age and fare

Just to double check my understanding, I also converted age and fare into z-scores and printed the before/after numbers, plus a before/after chart. As per my chart, the shape of the data looks the same, just the numbers on the x-axis change which confirmed the standardizing worked correctly.

---

## Part B - Building and testing the models (`02_modeling.ipynb`)

- Splitting the data: I used a stratified 80/20 split on survived, meaning both the train and test sets keep roughly the same 62%/38% mix of "did not survive" / "survived" that the full dataset has. I did this because a plain random split could by chance put too many or too few survivors in the test set, making the test results less trustworthy.
- Cleaning for the model: I used a ColumnTransformer (fills in missing numbers with the median and scales them, fills in missing categories with the most common one and turns them into columns of 0s and 1s) wrapped inside a Pipeline. This is fit only on the training data, then just applied to the test data, so nothing from the test set leaks into training. Columns used: age, fare, sibsp, parch, pclass, sex, embarked.

### Comparing the 3 models (on the test data)

| Model                   | Accuracy | Precision | Recall | F1    | AUC   |
| ----------------------- | -------- | --------- | ------ | ----- | ----- |
| Logistic Regression     | 0.804    | 0.793     | 0.667  | 0.724 | 0.844 |
| Decision Tree           | 0.816    | 0.773     | 0.739  | 0.756 | 0.797 |
| Random Forest (default) | 0.816    | 0.800     | 0.696  | 0.744 | 0.827 |
| Random Forest (tuned)   | 0.816    | 0.821     | 0.667  | 0.736 | 0.839 |

The notebook also has confusion matrices, ROC curves, and a picture of the Decision Tree with labeled features and classes. As per my ROC curve graph, Logistic Regression's line sits highest above the diagonal (matching its best AUC of 0.844), while the Decision Tree's line sits closest to the diagonal (matching its lowest AUC of 0.797), so the ROC picture and the table above agree with each other.

### Handling class imbalance (tested on Logistic Regression)

|                            | Precision | Recall | F1    |
| -------------------------- | --------- | ------ | ----- |
| Baseline (no fix)          | 0.793     | 0.667  | 0.724 |
| class_weight='balanced'    | 0.730     | 0.783  | 0.755 |
| SMOTE (training data only) | 0.740     | 0.783  | 0.761 |

As per my table above, both fixes give up a little bit of precision but gain a good amount of recall (going from 0.667 up to 0.783). SMOTE came out very slightly ahead on F1 score in my run. Since this dataset's imbalance isn't extreme (62/38, not like 95/5), either fix is a reasonable improvement over doing nothing.

### Tuning the Random Forest (GridSearchCV)

Best settings found: n_estimators=300, max_depth=10, max_features='sqrt'. OOB score: 0.823.

### Bonus task - predicting fare with regression

| MAE   | RMSE  | R²   | Adjusted R² |
| ----- | ----- | ----- | ------------ |
| 20.90 | 30.53 | 0.398 | 0.373        |

Heteroscedasticity check: as per my residual plot, the errors are not spread out evenly, they form a funnel shape, with small errors on the left side (low fares) that get much bigger and more spread out on the right side (high fares). This uneven, funnel shaped spread is called heteroscedasticity, and looking at my graph I can say this data does show it. It makes sense here because fare itself is very skewed (as shown earlier), with a handful of very expensive tickets that are harder for the model to predict exactly.

`titanic_pipeline.joblib` file holds both the cleaning steps and the tuned Random Forest model together, saved with joblib.dump(). I reloaded it with joblib.load() and tested it on two brand new, uncleaned passenger records to make sure it still works correctly end to end.

## Files in this folder

```
analytics/
├── 01_eda.ipynb              # Part A: load, look at, and clean the data, make the charts
├── 02_modeling.ipynb         # Part B: build and test the models
├── titanic.csv                # saved copy of the raw dataset
├── titanic_pipeline.joblib    # the saved model + cleaning steps together
├── requirements.txt
└── charts/                  
```
