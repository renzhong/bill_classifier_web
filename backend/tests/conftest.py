"""测试通用 fixture（M1 不强制 backend e2e，先留骨架）"""
import os

os.environ.setdefault("BCW_JWT_SECRET", "test-secret")
os.environ.setdefault("BCW_FERNET_KEY", "wfd6JLrx2VLDuJfm5RncRzCKqM8M9aFpaSGv4UCh-vM=")
