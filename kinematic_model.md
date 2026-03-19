### 运动学方程
$$ \mathbf{M\dot{\nu} + C(\nu)\nu + D(\nu)\nu = \tau} $$

其中各降维矩阵的物理意义如下：
* $\mathbf{\nu} = [u, v, r]^T$ 为 3-DOF 速度向量。
* $\mathbf{M} \in \mathbb{R}^{3\times3}$ 为总质量与惯性张量矩阵（包含附加质量）。该矩阵在配置脚本中设定。
* $\mathbf{C(\nu)} \in \mathbb{R}^{3\times3}$ 为科里奥利与向心力矩阵。该矩阵在配置脚本中设定。
* $\mathbf{D(\nu)} \in \mathbb{R}^{3\times3}$ 为水动力阻尼矩阵（通常包含线性和非线性阻尼项）。该矩阵在配置脚本中设定。
* $\mathbf{\tau} = [\tau_u, \tau_v, \tau_r]^T$ 为控制输入向量。env的设定中输入动作经过线性映射，变为$\tau_u,\tau_r$，$\tau_v$默认为0

#### 3.2 运动学方程 (Kinematics Equation)
描述船体局部坐标系下的速度 $\nu$ 如何通过旋转矩阵 $\mathbf{J(\eta)}$ 转换到全局坐标系下，从而更新 USV 的绝对位置 $\eta$：

$$ \mathbf{\dot{\eta} = J(\eta)\nu} $$

展开为标准矩阵形式为：
$$
\begin{bmatrix} \dot{x} \\ \dot{y} \\ \dot{\psi} \end{bmatrix} = 
\begin{bmatrix} 
\cos\psi & -\sin\psi & 0 \\
\sin\psi & \cos\psi & 0 \\
0 & 0 & 1 
\end{bmatrix}
\begin{bmatrix} u \\ v \\ r \end{bmatrix}
$$