class Panoptes < Formula
  desc "Local repository structure and retrieval CLI for coding agents"
  homepage "https://github.com/wallentx/panoptes"
  license "MIT"

  head do
    url "https://github.com/wallentx/panoptes.git", branch: "main"
    depends_on "rust" => :build
  end

  depends_on "git"

  on_macos do
    on_arm do
      url "https://github.com/wallentx/panoptes/releases/download/v1.0.4/panoptes-1.0.4-aarch64-apple-darwin.tar.gz"
      sha256 "91523b3d07532087e002c9c3bccd53f57247c7aea0d70661804580258493ff09"
    end

    on_intel do
      url "https://github.com/wallentx/panoptes/releases/download/v1.0.4/panoptes-1.0.4-x86_64-apple-darwin.tar.gz"
      sha256 "5280c19d98c744ed951534354643a3e136fc7b44df302a7e3f0eaa1daf0e4c02"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/wallentx/panoptes/releases/download/v1.0.4/panoptes-1.0.4-aarch64-unknown-linux-gnu.tar.gz"
      sha256 "e7d8af85046846a4bce8a12dc7539f9ca883b1f145d240e764182c60dcf46cbd"
    end

    on_intel do
      url "https://github.com/wallentx/panoptes/releases/download/v1.0.4/panoptes-1.0.4-x86_64-unknown-linux-gnu.tar.gz"
      sha256 "0ca3a3e5d02fa1091893fc3bc659ec0cb3e39672472629dba2ff5bcb478cba9e"
    end
  end

  def install
    if build.head?
      ENV["PANOPTES_GIT_SHA"] = Utils.git_head
      system "cargo", "install", *std_cargo_args
      generate_completions_from_executable(bin/"panoptes", "completions")
    else
      bin.install "panoptes"
      bash_completion.install "completions/panoptes.bash" => "panoptes"
      zsh_completion.install "completions/_panoptes"
      fish_completion.install "completions/panoptes.fish"
    end
  end

  def caveats
    <<~EOS
      Configure your coding agent after installation, for example:
        panoptes init --provider cursor --provider opencode

      After upgrades, rerun panoptes init for your providers and restart
      their MCP clients so they use the newly installed executable.
    EOS
  end

  test do
    unless build.head?
      metadata = JSON.parse(shell_output("#{bin}/panoptes version --json"))
      assert_equal version.to_s, metadata.fetch("version")
    end

    (testpath/"src/example.ts").write <<~TYPESCRIPT
      export function greet(name: string) { return "hello " + name; }
      export function main() { return greet("world"); }
    TYPESCRIPT
    system "git", "init", "--quiet", testpath

    store = testpath/"panoptes.db"
    system bin/"panoptes", "--store", store, "build", testpath
    results = JSON.parse(shell_output("#{bin}/panoptes --store #{store} grep greet --path #{testpath} --json"))
    assert_equal 1, results.length
    result = results.fetch(0)
    assert_equal 2, result.fetch("total_hits")
    assert_equal 0, result.fetch("unreadable")
    system bin/"panoptes", "--store", store, "check", testpath
  end
end
