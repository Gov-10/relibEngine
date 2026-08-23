"""Create all Auth DB tables from the SQLAlchemy models."""

from database import Base, engine

import models


def main():
    Base.metadata.create_all(bind=engine)
    print("Auth DB schema created:", ", ".join(sorted(Base.metadata.tables)))


if __name__ == "__main__":
    main()
