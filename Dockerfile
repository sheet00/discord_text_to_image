FROM python:latest

WORKDIR /app

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y \
    git \
    vim \
    curl \
    wget \
    build-essential \
    sudo \
    nodejs \
    npm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# タイムゾーンをJSTに設定
ENV TZ=Asia/Tokyo
RUN dpkg-reconfigure -f noninteractive tzdata

# ubuntuユーザーを作成
RUN id -u ubuntu || useradd -m -s /bin/bash ubuntu && \
    echo "ubuntu ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Claude Codeをグローバルインストール
RUN npm install -g @anthropic-ai/claude-code
    
# 作業ディレクトリを設定
WORKDIR /app

# ubuntuユーザーに切り替え
USER ubuntu

# requirements.txtをコピーしてインストール
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# gitの安全なディレクトリ設定
RUN git config --global --add safe.directory /app

# Claude Codeの設定
RUN claude config set --global preferredNotifChannel terminal_bell

# デフォルトコマンド
CMD ["/bin/bash"]