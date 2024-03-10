<template>
  <div class="app">
    <!-- 顶部菜单栏 -->
    <el-menu mode="horizontal" background-color="#545c64" text-color="#fff" active-text-color="#ffd04b">
      <el-menu-item index="1">菜单项1</el-menu-item>
      <el-menu-item index="2">菜单项2</el-menu-item>
      <el-menu-item index="3">菜单项3</el-menu-item>
    </el-menu>

    <div class="content">
      <!-- 左侧对象浏览列表 -->
      <div class="sidebar">
        <el-card>
          <div slot="header">对象浏览列表</div>
          <el-scrollbar style="height: calc(50vh - 40px); overflow-y: auto;">
            <el-tree :data="treeData" node-key="id" default-expand-all></el-tree>
          </el-scrollbar>
        </el-card>
      </div>

      <!-- 代码编辑窗口 -->
      <div class="code-editor">
        <el-card>
          <div slot="header">代码编辑窗口</div>
          <el-scrollbar style="height: calc(50vh - 40px); overflow-y: auto;">
            <el-input type="textarea" :rows="10" placeholder="请输入代码"></el-input>
          </el-scrollbar>
        </el-card>
      </div>

      <!-- 中央图像显示区域 -->
      <div class="image-display">
        <el-card>
          <div slot="header">中央图像显示区域</div>
          <div class="image-container">
            <img src="your-image-url.jpg" alt="中央图像">
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script>
import 'element-ui/lib/theme-chalk/index.css';
import { Menu, MenuItem, Tree, Card, Scrollbar, Input } from 'element-ui';

export default {
  components: {
    'el-menu': Menu,
    'el-menu-item': MenuItem,
    'el-tree': Tree,
    'el-card': Card,
    'el-scrollbar': Scrollbar,
    'el-input': Input
  },
  data() {
    return {
      treeData: [ /* 你的对象浏览列表数据 */ ]
    };
  }
};
</script>

<style>
.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
}
.content {
  display: flex;
  flex: 1;
}
.sidebar, .code-editor, .image-display {
  width: 33.33%;
  padding: 10px;
}
.image-container {
  text-align: center;
}
</style>
