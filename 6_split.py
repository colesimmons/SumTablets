import pandas as pd
from constants import OUTPUT_DIR
from sklearn.model_selection import train_test_split

INFILE = f"{OUTPUT_DIR}/5_with_glyphs.csv"


def main():
    df = pd.read_csv(INFILE, low_memory=False, encoding="utf-8")

    # Separate out the Lexical genre rows
    # We only want to use these for training
    lexical_df = df[df["genre"] == "Lexical"]
    non_lexical_df = df[df["genre"] != "Lexical"]

    # Split the dataframe into a train, test, and val sets
    # 95% train, 5% val, 5% test
    train_val_df, test_df = train_test_split(
        non_lexical_df,
        stratify=non_lexical_df["period"],
        test_size=0.05,
        random_state=42,
    )
    train_df, val_df = train_test_split(
        train_val_df,
        stratify=train_val_df["period"],
        test_size=(5 / 95),
        random_state=42,
    )
    train_df = pd.concat([train_df, lexical_df])

    print(f"Train: {len(train_df)}")
    print(f"Test: {len(test_df)}")
    print(f"Val: {len(val_df)}")

    for name, df in (("Train", train_df), ("Test", test_df), ("Val", val_df)):
        # Print how many examples we have for each period and genre
        print()
        print(f"-- {name} --")
        print(df["period"].value_counts())
        print()
        print(df["genre"].value_counts())
        print()

    # Shuffle em up
    train_df = train_df.sample(frac=1).reset_index(drop=True)
    test_df = test_df.sample(frac=1).reset_index(drop=True)
    val_df = val_df.sample(frac=1).reset_index(drop=True)

    # Write to csv
    train_df.to_csv(f"{OUTPUT_DIR}/train.csv", index=False, encoding="utf-8")
    val_df.to_csv(f"{OUTPUT_DIR}/validation.csv", index=False, encoding="utf-8")
    test_df.to_csv(f"{OUTPUT_DIR}/test.csv", index=False, encoding="utf-8")
    return


if __name__ == "__main__":
    main()
